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
        # Note: Pincc proxy currently crashes (422) if tools are provided in the Anthropic payload.
        # We temporarily disable sending tools to the LLM.
        tools = None

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

        # --- MANUAL TOOL TRIGGER FOR TESTING (Since proxy doesn't support tools) ---
        if "微信" in task and ("发" in task or "消息" in task):
            wechat_tool = self.tool_registry.get_tool("wechat_send_message")
            if wechat_tool:
                # Naive parsing just for the proof of concept testing
                contact = "文件传输助手"
                if "【" in task and "】" in task:
                    contact = task.split("【")[1].split("】")[0]
                
                msg_content = "测试消息"
                if "：" in task:
                    msg_content = task.split("：")[1]
                elif ":" in task:
                    msg_content = task.split(":")[1]

                result = await wechat_tool.execute(contact_name=contact, message=msg_content)
                return f"{response.content}\n\n[Agent Action] {result}"

        # Handle tool calls if any (Won't be hit while tools=None)
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
