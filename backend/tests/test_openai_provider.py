import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.llm.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_chat():
    """Test OpenAI-compatible provider chat method"""
    with patch('src.llm.openai_provider.AsyncOpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from OpenAI"
        mock_response.choices[0].finish_reason = "stop"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAIProvider(base_url="http://localhost:11434/v1", api_key="ollama")
        response = await provider.chat([{"role": "user", "content": "Hi"}])

        assert response.content == "Hello from OpenAI"
        assert response.finish_reason == "stop"
