import pytest
from src.tools.registry import ToolRegistry
from src.tools.base import Tool


def test_tool_registry_register():
    """Test registering a tool"""
    registry = ToolRegistry()

    class DummyTool(Tool):
        name = "dummy"
        description = "A dummy tool"

        async def execute(self, **kwargs):
            return "dummy result"

    tool = DummyTool()
    registry.register(tool)

    assert "dummy" in registry.list_tools()
    assert registry.get_tool("dummy") == tool
