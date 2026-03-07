from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import os
import asyncio
import json

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with Claude API integration via SSE streaming"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    
    from src.agent.computer_agent import run_agent

    async def event_generator():
        if not api_key:
            yield f"data: {json.dumps({'type': 'error', 'content': 'ANTHROPIC_API_KEY not configured'})}\n\n"
            return
            
        q = asyncio.Queue()
        
        def on_step(step, desc):
            try:
                safe_desc = desc.encode(os.sys.stdout.encoding or 'utf-8', 'ignore').decode(os.sys.stdout.encoding or 'utf-8', 'ignore')
                print(f"  [{step}] {safe_desc}")
            except Exception:
                pass
            # Push live update to frontend queue
            q.put_nowait({"type": "step", "content": f"Step {step}: {desc}"})
            
        async def run_task():
            try:
                try:
                    print(f"Starting optimized agent for task: {request.message}".encode('utf-8', 'ignore').decode('utf-8', 'ignore'))
                except Exception:
                    pass
                final_res = await run_agent(
                    task=request.message,
                    api_key=api_key,
                    base_url=base_url,
                    model="claude-sonnet-4-6",
                    on_step=on_step
                )
                q.put_nowait({"type": "result", "content": final_res})
            except Exception as e:
                import traceback
                traceback.print_exc()
                q.put_nowait({"type": "error", "content": str(e)})
            finally:
                q.put_nowait(None)
                
        # Run agent asynchronously allowing queue to pop
        loop_task = asyncio.create_task(run_task())
        
        while True:
            msg = await q.get()
            if msg is None:
                break
            yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
