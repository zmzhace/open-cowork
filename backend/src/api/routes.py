from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@router.post("/chat")
async def chat(message: str):
    """Chat endpoint"""
    # TODO: Implement chat logic
    return {"response": "Not implemented yet"}
