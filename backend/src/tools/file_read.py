from src.tools.base import Tool
from typing import Any


class FileReadTool(Tool):
    name = "file_read"
    description = "Read contents of a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read"
            }
        },
        "required": ["path"]
    }

    async def execute(self, path: str, **kwargs) -> Any:
        """Read file contents"""
        with open(path, 'r') as f:
            return f.read()
