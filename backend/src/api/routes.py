from fastapi import APIRouter
from pydantic import BaseModel
from src.llm.claude_provider import ClaudeProvider
from src.agent_manager import AgentManager
from src.tools.registry import ToolRegistry
from src.tools import WeChatSendMessageTool
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
    """Chat endpoint with Claude API integration"""
    try:
        # Get API configuration from environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        base_url = os.getenv("ANTHROPIC_BASE_URL")

        if not api_key:
            return {"response": "Error: ANTHROPIC_API_KEY not configured in .env file"}

        # Initialize Claude provider
        provider = ClaudeProvider(
            api_key=api_key,
            model="claude-sonnet-4-6",
            base_url=base_url
        )

        # Set up Tool Registry and register tools
        registry = ToolRegistry()
        registry.register(WeChatSendMessageTool())

        # Use AgentManager instead of calling provider directly to handle tool executions
        agent = AgentManager(provider=provider, tool_registry=registry)
        
        # Execute the task
        response_content = await agent.execute_task(request.message)

        return {"response": response_content}

    except Exception as e:
        return {"response": f"Error: {str(e)}"}
