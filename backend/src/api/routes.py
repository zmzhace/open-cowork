from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint"""
    # TODO: Implement full chat logic with LLM
    # For now, return a simple echo response
    return {"response": f"You said: {request.message}. (Backend connected! LLM integration coming soon...)"}
