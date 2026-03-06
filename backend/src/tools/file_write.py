from src.tools.base import Tool
from typing import Any


class FileWriteTool(Tool):
    name = "file_write"
    description = "Write content to a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["path", "content"]
    }

    async def execute(self, path: str, content: str, **kwargs) -> Any:
        """Write content to file"""
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
