import asyncio
import os
from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class WindowsMCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self._exit_stack = None
        self.tools_cache: List[Dict[str, Any]] = []
        
    async def connect(self):
        """Connect to the Windows-MCP server using uvx"""
        # Ensure uvx is in PATH or specify full path if needed.
        server_params = StdioServerParameters(
            command="uvx",
            args=["windows-mcp"],
            env=None # Inherit from OS
        )
        
        from contextlib import AsyncExitStack
        self._exit_stack = AsyncExitStack()
        
        try:
            stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
            self.session = await self._exit_stack.enter_async_context(ClientSession(stdio_transport[0], stdio_transport[1]))
            await self.session.initialize()
            print("Connected to Windows-MCP server.")
            
            # Fetch tools
            tools_response = await self.session.list_tools()
            self.tools_cache = []
            for tool in tools_response.tools:
                self.tools_cache.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                })
        except Exception as e:
            print(f"Failed to connect to Windows-MCP server: {e}")
            await self.close()
            raise

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Return cached tools in Anthropic's expected schema format."""
        anthropic_tools = []
        for t in self.tools_cache:
            anthropic_tools.append({
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"]
            })
        return anthropic_tools

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool via the MCP session"""
        if not self.session:
            raise RuntimeError("WindowsMCPClient is not connected.")
        
        try:
            result = await self.session.call_tool(name, arguments)
            
            # Normalize MCP result to a dictionary for our agent logic
            content_list = []
            for content in result.content:
                text_val = getattr(content, 'text', str(content))
                # Detect and strip massive base64 image strings from Snapshot Tool to prevent proxy 422 errors
                if name == "Snapshot" and "iVBOR" in text_val and len(text_val) > 10000:
                    text_val = "[Windows-MCP Base64 Image removed by proxy to save context limit. Please rely on the DOM/Textual data.]"
                
                content_list.append({"type": content.type, "text": text_val})

            tool_output = {
                "is_error": result.isError,
                "content": content_list
            }
            return tool_output
        except Exception as e:
            import traceback
            return {
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    async def close(self):
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
            self.session = None

# Global instance
mcp_client = WindowsMCPClient()
