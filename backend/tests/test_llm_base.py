import pytest
from src.llm.base import LLMProvider, LLMResponse


def test_llm_provider_interface():
    """Test that LLMProvider defines required interface"""
    assert hasattr(LLMProvider, 'chat')
    assert hasattr(LLMProvider, 'stream')
    assert hasattr(LLMProvider, 'get_capabilities')


def test_llm_response_structure():
    """Test LLMResponse data structure"""
    response = LLMResponse(
        content="Hello",
        tool_calls=None,
        finish_reason="stop"
    )
    assert response.content == "Hello"
    assert response.tool_calls is None
    assert response.finish_reason == "stop"
