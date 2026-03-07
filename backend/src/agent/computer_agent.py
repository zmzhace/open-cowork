# -*- coding: utf-8 -*-
"""
Computer Agent — ReAct agent loop with rich tool capabilities.
Uses Anthropic Claude with function-call tools for exec, screen, window, etc.
"""
import json
import os
import time
from typing import Optional
from anthropic import AsyncAnthropic

from src.agent.tools import (
    exec_tool,
    screen_tool,
    window_tool,
    process_tool,
    file_tool,
    clipboard_tool,
    app_finder_tool,
)

# All available tools
TOOLS = {
    "exec": exec_tool,
    "screen": screen_tool,
    "window": window_tool,
    "process": process_tool,
    "file": file_tool,
    "clipboard": clipboard_tool,
    "app_finder": app_finder_tool,
}

# Gather tool schemas
TOOL_SCHEMAS = [t.TOOL_SCHEMA for t in TOOLS.values()]

SYSTEM_PROMPT = """你是一个智能计算机操控助手，运行在 Windows 系统上。你可以通过工具来完成用户交给你的任何任务。

## 你的工具
- **exec** — 运行系统命令（启动程序、查状态、自动化操作）
- **screen** — 截屏、鼠标点击、键盘输入（用于 GUI 操作）
- **window** — 列出/聚焦/管理桌面窗口（包括隐藏在托盘的窗口）
- **process** — 查看/结束运行中的进程
- **file** — 读写文件
- **clipboard** — 读写剪贴板
- **app_finder** — 查找已安装的应用程序

## 打开/激活程序的步骤（非常重要！）
1. 先用 process(action="list", filter="程序名") 检查是否已经运行
2. 如果已运行，用 window(action="focus", title="窗口标题") 激活窗口（它会自动点击窗口中心）
3. 如果没有运行，用 app_finder(name="程序名") 找到安装路径，然后用 exec(command="start 路径") 启动
4. 桌面图标需要双击打开：screen(action="double_click", x=, y=)
5. 某些程序（如微信）可能隐藏在系统托盘，用 window(action="list") 可以找到隐藏窗口

## 使用 screen 工具的注意事项
- 截图会被缩放到1280px宽，工具会返回实际分辨率和缩放比例
- 给出的坐标应该是 **实际屏幕像素坐标**（按缩放比例换算）
- 例如：截图中看到目标在 x=400, y=300，缩放比例是 2.0，则实际坐标是 x=800, y=600
- 操作完成后截图确认结果

## 重要原则
- 优先使用 exec/window/process 等精确工具，screen 视觉操作作为补充
- 如果某个方法不工作（如窗口白屏），立刻换策略
- 遇到白屏窗口，尝试：关闭它然后重新打开、或者从系统托盘双击图标、或者用程序的全局快捷键
- 每次只做一个逻辑步骤，确认结果后再继续
"""


async def run_agent(
    task: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: str = "claude-sonnet-4-6",
    max_iterations: int = 50,
    on_step: callable = None,
) -> str:
    """
    Run the computer agent to complete a task.

    Args:
        task: The task description
        api_key: Anthropic API key (defaults to env var)
        base_url: API base URL (defaults to env var)
        model: Model to use
        max_iterations: Max agent loop iterations
        on_step: Optional callback(step_num, action_desc) for logging

    Returns:
        Final agent response text
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")

    if not api_key:
        return "Error: ANTHROPIC_API_KEY not set."

    if base_url:
        client = AsyncAnthropic(api_key=api_key, base_url=base_url)
    else:
        client = AsyncAnthropic(api_key=api_key)

    messages = [{"role": "user", "content": task}]

    # Loop detection
    recent_actions = []

    for iteration in range(max_iterations):
        if on_step:
            on_step(iteration + 1, "thinking...")

        try:
            response = await client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=TOOL_SCHEMAS,
            )
        except Exception as e:
            error_msg = str(e)
            if on_step:
                on_step(iteration + 1, f"API error: {error_msg[:100]}")
            return f"API Error: {error_msg}"

        # Add assistant response to history — convert to plain dicts to avoid serialization issues
        response_dicts = []
        for block in response.content:
            if hasattr(block, 'text') and block.type == "text":
                response_dicts.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                response_dicts.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        messages.append({"role": "assistant", "content": response_dicts})

        # Process response blocks
        tool_results = []
        pending_screenshots = []  # Screenshots to send after tool results
        final_text = ""

        for block in response.content:
            if hasattr(block, 'text') and block.text:
                final_text += block.text
                if on_step:
                    on_step(iteration + 1, f"💬 {block.text[:100]}")

            elif block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                if on_step:
                    on_step(iteration + 1, f"🔧 {tool_name}({json.dumps(tool_input, ensure_ascii=False)[:100]})")

                # Execute the tool
                tool_module = TOOLS.get(tool_name)
                if tool_module:
                    result = tool_module.execute(**tool_input)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}

                # Handle screenshot: extract image, send separately
                if tool_name == "screen" and tool_input.get("action") == "screenshot" and "image_base64" in result:
                    img_b64 = result.pop("image_base64")
                    pending_screenshots.append(img_b64)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

                # Loop detection
                action_key = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
                recent_actions.append(action_key)
                if len(recent_actions) > 5:
                    recent_actions = recent_actions[-5:]
                if len(recent_actions) >= 3 and len(set(recent_actions[-3:])) == 1:
                    if on_step:
                        on_step(iteration + 1, "⚠️ Loop detected!")
                    tool_results[-1]["content"] = json.dumps({
                        **result,
                        "_system_warning": "你已经重复执行了相同的操作3次。请换一种方法！"
                    }, ensure_ascii=False, default=str)

        # If no tools were used, Claude is done
        if not tool_results:
            if on_step:
                on_step(iteration + 1, "✅ Done")
            return final_text

        # Send tool results back to Claude
        messages.append({"role": "user", "content": tool_results})

        # If there were screenshots, inject them as a follow-up user message
        if pending_screenshots:
            screenshot_content = []
            for img_b64 in pending_screenshots:
                screenshot_content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": img_b64},
                })
            screenshot_content.append({
                "type": "text",
                "text": "以上是截图结果，请分析屏幕内容并继续执行任务。",
            })
            # Claude needs alternating user/assistant, so we add a brief assistant message first
            messages.append({"role": "assistant", "content": "我已收到截图，正在分析..."})
            messages.append({"role": "user", "content": screenshot_content})

        time.sleep(0.3)

    return f"Reached max iterations ({max_iterations}). Last response: {final_text}"
