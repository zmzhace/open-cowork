from fastapi import APIRouter
from pydantic import BaseModel
import os

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint — uses the optimized Computer Agent"""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        base_url = os.getenv("ANTHROPIC_BASE_URL")

        if not api_key:
            return {"response": "Error: ANTHROPIC_API_KEY not configured in .env file"}

        from src.agent.computer_agent import run_agent
        
        print(f"🚀 Starting optimized agent for task: {request.message}")
        
        response_content = await run_agent(
            task=request.message,
            api_key=api_key,
            base_url=base_url,
            model="claude-sonnet-4-6",
            on_step=lambda step, desc: print(f"  [{step}] {desc}")
        )
        
        return {"response": response_content}

    except Exception as e:
        return {"response": f"Error: {str(e)}"}

