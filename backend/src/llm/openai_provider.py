from typing import List, Dict, Any, Optional, AsyncIterator
from openai import AsyncOpenAI
from src.llm.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        api_key: str = "not-needed",
        model: str = "llama3"
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat request to OpenAI-compatible API"""
        params = {
            "model": self.model,
            "messages": messages
        }

        if tools:
            params["tools"] = tools

        response = await self.client.chat.completions.create(**params)

        message = response.choices[0].message
        tool_calls = None

        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_calls = [
                {
                    "name": tc.function.name,
                    "input": tc.function.arguments
                }
                for tc in message.tool_calls
            ]

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            finish_reason=response.choices[0].finish_reason
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from OpenAI-compatible API"""
        params = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }

        if tools:
            params["tools"] = tools

        stream = await self.client.chat.completions.create(**params)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI provider capabilities"""
        return {
            "provider": "openai-compatible",
            "model": self.model,
            "base_url": self.base_url,
            "supports_streaming": True,
            "supports_tools": True
        }
