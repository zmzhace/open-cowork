# -*- coding: utf-8 -*-
"""window tool — list/focus/manage windows using Win32 API."""
import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32


TOOL_SCHEMA = {
    "name": "window",
    "description": "Manage desktop windows: list all windows, focus/show/minimize/close a window by title or hwnd.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "focus", "minimize", "close"],
                "description": "Action to perform",
            },
            "title": {"type": "string", "description": "Window title (partial match) for focus/minimize/close"},
            "hwnd": {"type": "integer", "description": "Window handle (alternative to title)"},
        },
        "required": ["action"],
    },
}


def _enum_windows(visible_only=False):
    """Enumerate all windows with proper Unicode titles."""
    results = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            visible = bool(user32.IsWindowVisible(hwnd))
            if not visible_only or visible:
                results.append({
                    "hwnd": hwnd,
                    "title": buf.value,
                    "visible": visible,
                    "minimized": bool(user32.IsIconic(hwnd)),
                })
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return results


def _find_window(title=None, hwnd=None):
    """Find a window by title or hwnd."""
    windows = _enum_windows()
    if hwnd:
        return next((w for w in windows if w["hwnd"] == hwnd), None)
    if title:
        return next((w for w in windows if title in w["title"]), None)
    return None


def _activate(hwnd):
    """Bring window to foreground safely (move mouse, no auto-click)."""
    import pyautogui
    import time

    SW_SHOW, SW_RESTORE, SW_SHOWNORMAL = 5, 9, 1
    user32.ShowWindow(hwnd, SW_SHOW)
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    else:
        user32.ShowWindow(hwnd, SW_SHOWNORMAL)
    user32.keybd_event(0x12, 0, 0, 0)  # Alt down
    user32.SetForegroundWindow(hwnd)
    user32.keybd_event(0x12, 0, 2, 0)  # Alt up
    user32.BringWindowToTop(hwnd)

    # Get window position and move cursor to center (don't click to avoid hitting buttons)
    time.sleep(0.5)
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    cx = (rect.left + rect.right) // 2
    cy = (rect.top + rect.bottom) // 2
    if rect.right - rect.left > 50 and rect.bottom - rect.top > 50:
        pyautogui.moveTo(cx, cy)
        time.sleep(0.2)

    return {"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom}


def execute(action: str, title: str = None, hwnd: int = None, **kwargs) -> dict:
    if action == "list":
        windows = _enum_windows()
        # Filter to windows with actual titles, limit output to save tokens
        named = [w for w in windows if w["title"].strip()]
        # Sort by visibility (visible first) and limit to top 30
        named.sort(key=lambda w: (not w["visible"], w["title"]))
        named = named[:30]
        return {"windows": named, "count": len(named), "note": "Showing top 30 windows. Use title filter in focus/minimize/close."}

    elif action == "focus":
        w = _find_window(title, hwnd)
        if not w:
            return {"error": f"Window not found: title={title}, hwnd={hwnd}"}
        rect = _activate(w["hwnd"])
        return {
            "result": f"Focused window: {w['title']} and clicked center to activate rendering",
            "hwnd": w["hwnd"],
            "rect": rect,
        }

    elif action == "minimize":
        w = _find_window(title, hwnd)
        if not w:
            return {"error": f"Window not found"}
        user32.ShowWindow(w["hwnd"], 6)  # SW_MINIMIZE
        return {"result": f"Minimized: {w['title']}"}

    elif action == "close":
        w = _find_window(title, hwnd)
        if not w:
            return {"error": f"Window not found"}
        WM_CLOSE = 0x0010
        user32.PostMessageW(w["hwnd"], WM_CLOSE, 0, 0)
        return {"result": f"Sent close to: {w['title']}"}

    return {"error": f"Unknown action: {action}"}
