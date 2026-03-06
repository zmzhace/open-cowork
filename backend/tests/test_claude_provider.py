import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.llm.claude_provider import ClaudeProvider


@pytest.mark.asyncio
async def test_claude_chat():
    """Test Claude provider chat method"""
    with patch('src.llm.claude_provider.AsyncAnthropic') as mock_anthropic:
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Mock the messages.create response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello from Claude")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = ClaudeProvider(api_key="test-key")
        response = await provider.chat([{"role": "user", "content": "Hi"}])

        assert response.content == "Hello from Claude"
        assert response.finish_reason == "end_turn"
