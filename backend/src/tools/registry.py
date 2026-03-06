from typing import Dict, List, Optional
from src.tools.base import Tool


class ToolRegistry:
    """Registry for managing tools"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool"""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools"""
        return list(self._tools.values())

    def to_llm_format(self) -> List[Dict]:
        """Convert all tools to LLM format"""
        return [tool.to_dict() for tool in self._tools.values()]
