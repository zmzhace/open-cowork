import pytest
from src.agent_manager import AgentManager
from src.llm.base import LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    async def chat(self, messages, tools=None, **kwargs):
        return LLMResponse(content="Mock response", finish_reason="stop")

    async def stream(self, messages, tools=None, **kwargs):
        yield "Mock"
        yield " response"

    def get_capabilities(self):
        return {"provider": "mock"}


@pytest.mark.asyncio
async def test_agent_manager_execute():
    """Test agent manager execution"""
    provider = MockProvider()
    manager = AgentManager(provider)

    response = await manager.execute_task("Test task")

    assert "Mock response" in response
