from typing import List, Dict, Any, Optional, AsyncIterator
from anthropic import Anthropic, AsyncAnthropic
from src.llm.base import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat request to Claude API"""
        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096)
        }

        if tools:
            params["tools"] = tools

        response = await self.client.messages.create(**params)

        # Extract text content
        content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                content += block.text

        # Extract tool calls if any
        tool_calls = None
        if hasattr(response, 'tool_use'):
            tool_calls = [
                {
                    "name": tool.name,
                    "input": tool.input
                }
                for tool in response.tool_use
            ]

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from Claude API"""
        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True
        }

        if tools:
            params["tools"] = tools

        async with self.client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                yield text

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Claude provider capabilities"""
        return {
            "provider": "claude",
            "model": self.model,
            "supports_streaming": True,
            "supports_tools": True,
            "supports_vision": True,
            "max_tokens": 200000
        }
