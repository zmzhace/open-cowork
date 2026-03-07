# -*- coding: utf-8 -*-
"""screen tool — screenshot + mouse/keyboard interaction."""
import base64
import io
import time
import mss
from PIL import Image
import pyautogui
import pyperclip

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1


TOOL_SCHEMA = {
    "name": "screen",
    "description": "Interact with the screen: take screenshots, click, type, scroll, press keys, and wait. Coordinates are in actual screen pixels.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["screenshot", "click", "double_click", "right_click", "type", "hotkey", "press", "scroll", "move", "drag", "wait"],
                "description": "The action to perform",
            },
            "x": {"type": "integer", "description": "X coordinate (for click/scroll/move/drag)"},
            "y": {"type": "integer", "description": "Y coordinate (for click/scroll/move/drag)"},
            "end_x": {"type": "integer", "description": "End X coordinate (for drag)"},
            "end_y": {"type": "integer", "description": "End Y coordinate (for drag)"},
            "text": {"type": "string", "description": "Text to type (for 'type' action) or key name (for 'press' action)"},
            "keys": {"type": "array", "items": {"type": "string"}, "description": "Key combination (for 'hotkey', e.g. ['ctrl', 'f'])"},
            "amount": {"type": "integer", "description": "Scroll amount (positive=up, negative=down, default -3) OR wait amount in seconds (for 'wait' action)"},
            "monitor": {"type": "integer", "description": "Monitor index (1=primary, 2=secondary, default 1)"},
        },
        "required": ["action"],
    },
}


def _take_screenshot(monitor_idx: int = 1) -> str:
    """Take screenshot, return base64 PNG. Supports multi-monitor."""
    with mss.mss() as sct:
        if monitor_idx < 1 or monitor_idx >= len(sct.monitors):
            monitor_idx = 1
        monitor = sct.monitors[monitor_idx]
        img = sct.grab(monitor)
        pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        # Resize for efficiency
        max_w = 1280
        if pil_img.width > max_w:
            ratio = max_w / pil_img.width
            pil_img = pil_img.resize((max_w, int(pil_img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG", optimize=True)
        return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def get_screen_size() -> tuple:
    with mss.mss() as sct:
        m = sct.monitors[1]
        return m["width"], m["height"]


def execute(action: str, x: int = None, y: int = None, text: str = None,
            keys: list = None, amount: int = -3, monitor: int = 1,
            end_x: int = None, end_y: int = None, **kwargs) -> dict:
    """Execute a screen action."""
    if action == "screenshot":
        img_b64 = _take_screenshot(monitor)
        w, h = get_screen_size()
        return {
            "type": "screenshot",
            "image_base64": img_b64,
            "screen_width": w,
            "screen_height": h,
            "note": f"Screenshot captured. Screen is {w}x{h}. Image is scaled to 1280px wide — multiply coordinates by {w/1280:.2f} to get real pixel positions.",
        }

    elif action == "click":
        pyautogui.click(x, y)
        time.sleep(0.3)  # Wait for UI to respond
        return {"result": f"Clicked at ({x}, {y})"}

    elif action == "double_click":
        pyautogui.doubleClick(x, y)
        time.sleep(0.3)
        return {"result": f"Double-clicked at ({x}, {y})"}

    elif action == "right_click":
        pyautogui.rightClick(x, y)
        time.sleep(0.3)
        return {"result": f"Right-clicked at ({x}, {y})"}

    elif action == "type":
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        return {"result": f"Typed: {text}"}

    elif action == "hotkey":
        pyautogui.hotkey(*keys)
        time.sleep(0.2)
        return {"result": f"Pressed hotkey: {'+'.join(keys)}"}

    elif action == "press":
        pyautogui.press(text)
        time.sleep(0.2)
        return {"result": f"Pressed key: {text}"}

    elif action == "scroll":
        pyautogui.scroll(amount, x=x, y=y)
        time.sleep(0.3)
        return {"result": f"Scrolled {amount} at ({x}, {y})"}

    elif action == "move":
        pyautogui.moveTo(x, y)
        return {"result": f"Moved cursor to ({x}, {y})"}

    elif action == "drag":
        if end_x is not None and end_y is not None:
            pyautogui.moveTo(x, y)
            pyautogui.drag(end_x - x, end_y - y, duration=0.5)
            time.sleep(0.3)
            return {"result": f"Dragged from ({x}, {y}) to ({end_x}, {end_y})"}
        return {"error": "drag requires end_x and end_y"}

    elif action == "wait":
        wait_time = amount if amount > 0 else 2
        time.sleep(wait_time)
        return {"result": f"Waited for {wait_time} seconds."}

    return {"error": f"Unknown action: {action}"}
