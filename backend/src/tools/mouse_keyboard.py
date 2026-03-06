from src.tools.base import Tool
from typing import Any
import pyautogui


class MouseMoveTool(Tool):
    name = "mouse_move"
    description = "Move mouse to coordinates"
    parameters = {
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"}
        },
        "required": ["x", "y"]
    }

    async def execute(self, x: int, y: int, **kwargs) -> Any:
        """Move mouse to position"""
        pyautogui.moveTo(x, y)
        return f"Moved mouse to ({x}, {y})"


class MouseClickTool(Tool):
    name = "mouse_click"
    description = "Click mouse at current position"
    parameters = {
        "type": "object",
        "properties": {
            "button": {
                "type": "string",
                "enum": ["left", "right", "middle"],
                "description": "Mouse button to click"
            }
        }
    }

    async def execute(self, button: str = "left", **kwargs) -> Any:
        """Click mouse button"""
        pyautogui.click(button=button)
        return f"Clicked {button} mouse button"


class KeyboardTypeTool(Tool):
    name = "keyboard_type"
    description = "Type text using keyboard"
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to type"}
        },
        "required": ["text"]
    }

    async def execute(self, text: str, **kwargs) -> Any:
        """Type text"""
        pyautogui.write(text)
        return f"Typed: {text}"
