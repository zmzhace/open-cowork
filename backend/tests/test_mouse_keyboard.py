import pytest
from unittest.mock import patch, MagicMock
import sys

# Mock pyautogui before importing the module
sys.modules['pyautogui'] = MagicMock()

from src.tools.mouse_keyboard import MouseMoveTool, KeyboardTypeTool


@pytest.mark.asyncio
async def test_mouse_move_tool():
    """Test mouse move tool"""
    with patch('src.tools.mouse_keyboard.pyautogui') as mock_gui:
        tool = MouseMoveTool()
        await tool.execute(x=100, y=200)

        mock_gui.moveTo.assert_called_once_with(100, 200)


@pytest.mark.asyncio
async def test_keyboard_type_tool():
    """Test keyboard type tool"""
    with patch('src.tools.mouse_keyboard.pyautogui') as mock_gui:
        tool = KeyboardTypeTool()
        await tool.execute(text="Hello")

        mock_gui.write.assert_called_once_with("Hello")
