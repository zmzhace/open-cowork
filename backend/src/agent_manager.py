from typing import List, Dict, Any, Optional
from src.llm.base import LLMProvider
from src.tools.registry import ToolRegistry


class AgentManager:
    """Manage agent execution and tool coordination"""

    def __init__(self, provider: LLMProvider, tool_registry: Optional[ToolRegistry] = None):
        self.provider = provider
        self.tool_registry = tool_registry or ToolRegistry()
        self.conversation_history: List[Dict[str, str]] = []

    async def execute_task(self, task: str) -> str:
        """Execute a task using the LLM and tools"""
        # Add user message
        self.conversation_history.append({
            "role": "user",
            "content": task
        })

        # Get tools in LLM format
        tools = self.tool_registry.to_llm_format() if self.tool_registry.list_tools() else None

        # Call LLM
        response = await self.provider.chat(
            messages=self.conversation_history,
            tools=tools
        )

        # Add assistant response
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        # Handle tool calls if any
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool = self.tool_registry.get_tool(tool_call["name"])
                if tool:
                    result = await tool.execute(**tool_call["input"])
                    # Add tool result to conversation
                    self.conversation_history.append({
                        "role": "user",
                        "content": f"Tool {tool_call['name']} result: {result}"
                    })

        return response.content

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
