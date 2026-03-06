from src.tools.base import Tool
from typing import Any
import mss
import tempfile
import os


class ScreenshotTool(Tool):
    name = "screenshot"
    description = "Take a screenshot of the screen"
    parameters = {
        "type": "object",
        "properties": {}
    }

    async def execute(self, **kwargs) -> Any:
        """Take a screenshot"""
        with mss.mss() as sct:
            # Take screenshot of primary monitor
            output_path = os.path.join(tempfile.gettempdir(), "screenshot.png")
            sct.shot(output=output_path)
            return f"Screenshot saved to {output_path}"
