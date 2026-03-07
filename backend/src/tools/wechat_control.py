from src.tools.base import Tool
from typing import Any, Optional
import pyautogui
import pyperclip
import time
import subprocess
import ctypes
import ctypes.wintypes
import os
import base64
import json
import mss
import io
from anthropic import AsyncAnthropic


# ─── Windows API helpers ───
user32 = ctypes.windll.user32

def find_window_by_title(keyword: str):
    """Find a window whose title contains the given keyword (including hidden windows)."""
    result = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

    def enum_callback(hwnd, _lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            if keyword in title:
                result.append((hwnd, title))
        return True

    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    return result


def activate_window(hwnd):
    """Bring a window to the foreground, even if hidden in system tray."""
    SW_SHOW = 5
    SW_RESTORE = 9
    SW_SHOWNORMAL = 1

    # Show the window first (in case it's hidden in tray)
    user32.ShowWindow(hwnd, SW_SHOW)
    # Restore if minimized
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    else:
        user32.ShowWindow(hwnd, SW_SHOWNORMAL)

    # Windows blocks SetForegroundWindow for background processes.
    # Workaround: simulate an Alt key press to trick Windows into allowing it.
    user32.keybd_event(0x12, 0, 0, 0)  # Alt key down
    user32.SetForegroundWindow(hwnd)
    user32.keybd_event(0x12, 0, 2, 0)  # Alt key up

    # Additional attempt
    user32.BringWindowToTop(hwnd)


WECHAT_PATHS = [
    r"D:\WeChat\WeChat.exe",
    r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
    r"C:\Program Files\Tencent\WeChat\WeChat.exe",
]


def find_wechat_exe():
    for path in WECHAT_PATHS:
        if os.path.exists(path):
            return path
    return None


# ─── Vision Agent ───
def take_screenshot_base64() -> str:
    """Take a screenshot and return as base64-encoded PNG."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Primary monitor
        img = sct.grab(monitor)
        # Convert to PNG bytes
        from PIL import Image
        pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")


SYSTEM_PROMPT = """你是一个计算机操作助手。你通过分析屏幕截图来执行用户任务。

你每次会收到一张屏幕截图。请返回一个JSON操作指令。

可用操作：
- {"action": "click", "x": 数字, "y": 数字, "description": "说明"}
- {"action": "type", "text": "文字", "description": "说明"}
- {"action": "hotkey", "keys": ["ctrl", "f"], "description": "说明"}
- {"action": "press", "key": "enter", "description": "说明"}
- {"action": "done", "description": "完成说明"}
- {"action": "error", "description": "错误说明"}

【极其重要】你必须只返回一个JSON对象，不允许有任何其他文字！不要有分析过程！不要有markdown！只有纯JSON！"""


def extract_json(text: str) -> dict:
    """Extract a JSON object from text, with repair for common LLM errors."""
    import re
    text = text.strip()

    # Remove markdown code blocks
    if "```" in text:
        match = re.search(r'```(?:json)?\s*(.*?)```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find JSON-like content
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        json_str = match.group()

        # Try direct parse
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Repair common issues:
        # 1. Fix unquoted keys like { action: "click", x: 100 }
        repaired = re.sub(r'(?<=[{,])\s*(\w+)\s*:', r' "\1":', json_str)
        # 2. Fix missing quote before key like: , y": 100 -> , "y": 100
        repaired = re.sub(r',\s*(\w+)":', r', "\1":', repaired)
        # 3. Remove trailing commas before }
        repaired = re.sub(r',\s*}', '}', repaired)

        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    return {"action": "error", "description": f"Cannot parse JSON from: {text[:200]}"}


async def vision_agent_step(
    client: AsyncAnthropic,
    model: str,
    task: str,
    screenshot_b64: str,
    history: list
) -> dict:
    """Send screenshot to Claude and get the next action."""
    user_message = {
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_b64
                }
            },
            {
                "type": "text",
                "text": f"任务：{task}\n返回下一步操作JSON："
            }
        ]
    }

    messages = history + [user_message]

    response = await client.messages.create(
        model=model,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=messages
    )

    response_text = ""
    for block in response.content:
        if hasattr(block, 'text'):
            response_text += block.text

    return extract_json(response_text)


def execute_action(action: dict) -> str:
    """Execute an action returned by the vision agent."""
    act = action.get("action", "")
    desc = action.get("description", "")

    if act == "click":
        x, y = action["x"], action["y"]
        pyautogui.click(x, y)
        return f"Clicked at ({x}, {y}): {desc}"

    elif act == "type":
        text = action["text"]
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        return f"Typed: {text}: {desc}"

    elif act == "hotkey":
        keys = action["keys"]
        pyautogui.hotkey(*keys)
        return f"Pressed hotkey {'+'.join(keys)}: {desc}"

    elif act == "press":
        key = action["key"]
        pyautogui.press(key)
        return f"Pressed {key}: {desc}"

    elif act == "done":
        return f"DONE: {desc}"

    elif act == "error":
        return f"ERROR: {desc}"

    else:
        return f"Unknown action: {act}"


class WeChatSendMessageTool(Tool):
    name = "wechat_send_message"
    description = "Open WeChat (微信), search for a contact, and send them a message using vision-based AI control."
    parameters = {
        "type": "object",
        "properties": {
            "contact_name": {"type": "string", "description": "The name of the contact or group to search for"},
            "message": {"type": "string", "description": "The message content to send"}
        },
        "required": ["contact_name", "message"]
    }

    async def execute(self, contact_name: str, message: str, **kwargs) -> Any:
        """Use vision-agent loop to send a WeChat message."""
        try:
            # 1. Open/Focus WeChat
            matches = find_window_by_title("微信")
            if matches:
                hwnd, title = matches[0]
                activate_window(hwnd)
                time.sleep(1)
            else:
                exe_path = find_wechat_exe()
                if not exe_path:
                    return "Error: Cannot find WeChat.exe."
                subprocess.Popen([exe_path])
                time.sleep(5)
                matches = find_window_by_title("微信")
                if matches:
                    activate_window(matches[0][0])
                    time.sleep(1)
                else:
                    return "Error: Launched WeChat but cannot find its window."

            # 2. Initialize Claude client for vision
            api_key = os.getenv("ANTHROPIC_API_KEY")
            base_url = os.getenv("ANTHROPIC_BASE_URL")
            if not api_key:
                return "Error: ANTHROPIC_API_KEY not set."

            if base_url:
                client = AsyncAnthropic(api_key=api_key, base_url=base_url)
            else:
                client = AsyncAnthropic(api_key=api_key)

            model = "claude-sonnet-4-6"
            task = f"在微信中找到联系人「{contact_name}」，打开与他的聊天窗口，发送消息：「{message}」"

            # 3. Vision agent loop
            history = []
            max_steps = 10
            log = []
            prev_actions = []  # Track recent actions for loop detection

            for step in range(max_steps):
                time.sleep(1.5)  # Wait for UI to settle

                # Take screenshot
                screenshot_b64 = take_screenshot_base64()

                # Build context about previous actions to avoid loops
                prev_context = ""
                if prev_actions:
                    prev_context = "\n你之前已经执行的操作：" + "; ".join(prev_actions[-3:])
                    # Detect if stuck in a loop
                    if len(prev_actions) >= 2 and prev_actions[-1] == prev_actions[-2]:
                        prev_context += "\n【警告】你在重复同一操作！请换一种方法。如果微信窗口没有打开，试一试搜索功能或点击其他位置。"

                # Ask Claude what to do
                action = await vision_agent_step(client, model, task + prev_context, screenshot_b64, history)

                # Log the action
                action_desc = action.get("description", str(action))
                log.append(f"Step {step + 1}: {action.get('action', '?')} - {action_desc}")

                if action["action"] == "done":
                    return f"Successfully completed task.\nLog:\n" + "\n".join(log)

                if action["action"] == "error":
                    return f"Agent error: {action_desc}\nLog:\n" + "\n".join(log)

                # Execute the action
                result = execute_action(action)
                log.append(f"  -> {result}")

                # Track for loop detection
                action_key = f"{action.get('action')}@{action.get('x','')},{action.get('y','')}{action.get('key','')}{action.get('text','')}"
                prev_actions.append(action_key)

                # Add to history for context (text only, not images, to save tokens)
                history.append({
                    "role": "user",
                    "content": f"[截图已发送] 当前任务：{task}"
                })
                history.append({
                    "role": "assistant",
                    "content": json.dumps(action, ensure_ascii=False)
                })

            return f"Reached max steps ({max_steps}).\nLog:\n" + "\n".join(log)

        except Exception as e:
            import traceback
            return f"Error: {str(e)}\n{traceback.format_exc()}"
