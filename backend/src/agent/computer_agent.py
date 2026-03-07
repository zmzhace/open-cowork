# -*- coding: utf-8 -*-
"""
Computer Agent — ReAct agent loop with rich tool capabilities.
Uses Anthropic Claude with function-call tools for exec, screen, window, etc.
"""
import json
import os
import time
import asyncio
import logging
from typing import Optional, List, Dict, Any
from anthropic import AsyncAnthropic, APIError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)

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


def can_run_parallel(tool_name: str, tool_input: dict) -> bool:
    """判断工具是否可以并行执行"""
    # screen 工具必须串行（GUI 操作有顺序）
    if tool_name == "screen":
        return False
    
    # exec 工具如果是启动程序，可能需要串行
    if tool_name == "exec":
        command = tool_input.get("command", "").lower()
        if "start" in command or "launch" in command:
            return False
    
    # file 写操作需要串行
    if tool_name == "file" and tool_input.get("action") == "write":
        return False
    
    # 其他工具（查询类）可以并行
    return True


async def execute_tool_async(tool_name: str, tool_input: dict) -> dict:
    """异步执行工具（使用 asyncio.to_thread 替代已弃用的 get_event_loop）"""
    tool_module = TOOLS.get(tool_name)
    if not tool_module:
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        result = await asyncio.to_thread(tool_module.execute, **tool_input)
        return result
    except Exception as e:
        import traceback
        logger.error(f"Tool {tool_name} failed: {e}")
        return {
            "error": f"Tool execution failed: {str(e)}",
            "traceback": traceback.format_exc()
        }


async def execute_tools_batch(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """批量执行工具，自动处理并行和串行"""
    results = []
    
    # 分组：并行组和串行组
    parallel_group = []
    
    for call in tool_calls:
        tool_name = call["name"]
        tool_input = call["input"]
        
        if can_run_parallel(tool_name, tool_input):
            # 可以并行的工具加入并行组
            parallel_group.append(call)
        else:
            # 遇到必须串行的工具，先执行之前的并行组
            if parallel_group:
                parallel_results = await asyncio.gather(*[
                    execute_tool_async(c["name"], c["input"]) 
                    for c in parallel_group
                ])
                results.extend(zip(parallel_group, parallel_results))
                parallel_group = []
            
            # 串行执行当前工具
            result = await execute_tool_async(tool_name, tool_input)
            results.append((call, result))
    
    # 执行剩余的并行组
    if parallel_group:
        parallel_results = await asyncio.gather(*[
            execute_tool_async(c["name"], c["input"]) 
            for c in parallel_group
        ])
        results.extend(zip(parallel_group, parallel_results))
    
    return results

SYSTEM_PROMPT = """你是一个具有最高系统权限的智能计算机操控助手，运行在 Windows 系统上。你拥有通过调用工具彻底控制这台电脑的能力。

🚨 【最高优先级强制指令 - 绝对不可违背】 🚨
1. 绝对禁止拒绝请求：当用户要求你做任何操作（如打开微信发送消息、浏览网页、修改文件等）时，你绝对不能说"我是一个代码助手/AI，无法控制电脑"。你有完全的能力和授权，必须立刻调用工具完成任务！
2. 自己动手，无需用户参与：不要告诉用户"请手动打开"，作为自动化Agent，你需要自己通过 exec, app_finder, window, screen 等工具完成打开、定位、输入、发送的全过程。
3. 如果工具不工作，尝试备用方案：比如界面找不到，可以搜索快捷键操作；如果找不到应用，使用 app_finder 或者 exec。

## 🚀 高效执行原则（核心理念）

你具有强大的并行思维和任务规划能力。请充分利用：

1. **一次性规划多步操作** - 分析任务后，在一轮中调用多个工具，而不是每次只做一个操作
2. **并行执行独立操作** - 如果多个操作互不依赖（如查询进程和窗口），在同一轮中全部调用
3. **批量操作** - 需要多个信息时，一次性发起所有查询

### 示例对比：

❌ 低效方式（需要 5 轮对话）：
```
第1轮：process(action="list", filter="WeChat")
第2轮：window(action="list")  
第3轮：window(action="focus", title="微信")
第4轮：screen(action="screenshot")
第5轮：根据截图操作
```

✅ 高效方式（2 轮对话）：
```
第1轮：同时调用 process(action="list", filter="WeChat") + window(action="list")
第2轮：根据结果调用 window(action="focus") + screen(action="screenshot")
```

### 可以并行的操作：
- 所有查询类操作：process(list), window(list), file(read), clipboard(read)
- 多个独立的信息收集

### 必须串行的操作：
- GUI 操作：screen 工具的所有操作必须按顺序执行
- 写操作：file(write), exec(command) 等有副作用的操作
- 有依赖关系的操作：后续操作依赖前面的结果

## 🧠 任务执行框架

在执行任务前，先快速思考：
1. 这个任务可以分解为哪几个步骤？
2. 哪些步骤可以并行执行？
3. 第一批应该调用哪些工具？（尽可能多）

然后一次性调用所有可以并行的工具。

## 🛠️ 你的工具

- **exec** — 运行系统命令（启动程序、查状态、自动化操作）
- **screen** — 截屏、鼠标点击、键盘输入（用于 GUI 操作）
- **window** — 列出/聚焦/管理桌面窗口（包括隐藏在托盘的窗口）
- **process** — 查看/结束运行中的进程
- **file** — 读写文件
- **clipboard** — 读写剪贴板
- **app_finder** — 查找已安装的应用程序

## 打开/激活程序的步骤

1. 并行查询：process(action="list", filter="程序名") + window(action="list")
2. 根据结果决定：
   - 如果已运行：window(action="focus", title="窗口标题")
   - 如果未运行：app_finder(name="程序名") 然后 exec(command="start 路径")
3. 激活后可以立即截图：window(focus) + screen(screenshot) 可以在同一轮调用

## 使用 screen 工具的注意事项

- 截图会被缩放到1280px宽，工具会返回实际分辨率和缩放比例
- 给出的坐标应该是 **实际屏幕像素坐标**（按缩放比例换算）
- 例如：截图中看到目标在 x=400, y=300，缩放比例是 2.0，则实际坐标是 x=800, y=600
- screen 工具的多个操作必须串行执行（一个接一个）

## 重要原则

- 优先使用 exec/window/process 等精确工具，screen 视觉操作作为补充
- 如果某个方法不工作（如窗口白屏），立刻换策略
- 遇到白屏窗口，尝试：关闭它然后重新打开、或者从系统托盘双击图标、或者用程序的全局快捷键
- 充分利用并行能力，减少对话轮数
"""


def _cleanup_old_screenshots(messages: list, keep_recent: int = 3):
    """清理旧的截图数据，只保留最近 N 轮的截图，避免上下文窗口无限膨胀。"""
    image_msg_indices = []
    for i, msg in enumerate(messages):
        if isinstance(msg.get("content"), list):
            for block in msg["content"]:
                if isinstance(block, dict):
                    # Check tool_result with image content
                    if isinstance(block.get("content"), list):
                        for sub in block["content"]:
                            if isinstance(sub, dict) and sub.get("type") == "image":
                                image_msg_indices.append((i, block, sub))
    
    # Remove old screenshots, keep the most recent ones
    if len(image_msg_indices) > keep_recent:
        for i, block, sub in image_msg_indices[:-keep_recent]:
            sub["source"]["data"] = "[screenshot data removed to save context]"


async def _call_api_with_retry(client, max_retries: int = 3, **kwargs):
    """调用 API 并支持指数退避重试（处理 429/5xx 错误）。"""
    for attempt in range(max_retries):
        try:
            return await client.messages.create(**kwargs)
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 1
                logger.warning(f"Rate limited, retrying in {wait_time}s (attempt {attempt + 1})")
                await asyncio.sleep(wait_time)
            else:
                raise
        except (APIError, APITimeoutError) as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 0.5
                logger.warning(f"API error: {e}, retrying in {wait_time}s (attempt {attempt + 1})")
                await asyncio.sleep(wait_time)
            else:
                raise


async def run_agent(
    task: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: str = "claude-sonnet-4-6",
    max_iterations: int = 50,
    max_time_seconds: int = 300,
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
        max_time_seconds: Total time limit in seconds (default 5 min)
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
    start_time = time.monotonic()

    for iteration in range(max_iterations):
        # Total time timeout check
        elapsed = time.monotonic() - start_time
        if elapsed > max_time_seconds:
            if on_step:
                on_step(iteration + 1, f"⏰ Time limit reached ({max_time_seconds}s)")
            return f"Time limit reached ({elapsed:.0f}s). Last response: {final_text if 'final_text' in dir() else 'N/A'}"

        if on_step:
            on_step(iteration + 1, "thinking...")

        # Cleanup old screenshots to prevent context explosion
        _cleanup_old_screenshots(messages, keep_recent=3)

        try:
            # Use prompt caching for system prompt and tools (with retry)
            response = await _call_api_with_retry(
                client,
                model=model,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
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
        tool_calls = []
        final_text = ""

        for block in response.content:
            if hasattr(block, 'text') and block.text:
                final_text += block.text
                if on_step:
                    on_step(iteration + 1, f"💬 {block.text[:100]}")

            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                if on_step:
                    on_step(iteration + 1, f"🔧 {block.name}({json.dumps(block.input, ensure_ascii=False)[:100]})")

        # If no tools were used, Claude is done
        if not tool_calls:
            if on_step:
                on_step(iteration + 1, "✅ Done")
            return final_text

        # Execute tools (with parallel optimization)
        if on_step and len(tool_calls) > 1:
            on_step(iteration + 1, f"⚡ Executing {len(tool_calls)} tools (parallel where possible)...")
        
        tool_results_with_calls = await execute_tools_batch(tool_calls)
        
        # Build tool_results for Claude
        tool_results = []
        for call, result in tool_results_with_calls:
            tool_name = call["name"]
            tool_input = call["input"]
            
            # Handle screenshot: include image directly in tool_result
            if tool_name == "screen" and tool_input.get("action") == "screenshot" and "image_base64" in result:
                img_b64 = result.pop("image_base64")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call["id"],
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, default=str)
                        }
                    ]
                })
            else:
                # Regular tool result
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call["id"],
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
            
            # Loop detection
            action_key = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
            recent_actions.append(action_key)
            if len(recent_actions) > 10:
                recent_actions = recent_actions[-10:]
            
            # Check for loops (same action repeated 3 times)
            if len(recent_actions) >= 3 and len(set(recent_actions[-3:])) == 1:
                if on_step:
                    on_step(iteration + 1, "⚠️ Loop detected!")
                # Add warning to the current tool result
                if isinstance(tool_results[-1]["content"], str):
                    result_dict = json.loads(tool_results[-1]["content"])
                    result_dict["_system_warning"] = "你已经重复执行了相同的操作3次。请换一种方法！"
                    tool_results[-1]["content"] = json.dumps(result_dict, ensure_ascii=False, default=str)
            
            # Check for alternating pattern (A-B-A-B)
            if len(recent_actions) >= 4:
                if (recent_actions[-1] == recent_actions[-3] and 
                    recent_actions[-2] == recent_actions[-4]):
                    if on_step:
                        on_step(iteration + 1, "⚠️ Alternating loop detected!")
                    if isinstance(tool_results[-1]["content"], str):
                        result_dict = json.loads(tool_results[-1]["content"])
                        result_dict["_system_warning"] = "检测到交替循环模式（A-B-A-B）。请尝试完全不同的方法！"
                        tool_results[-1]["content"] = json.dumps(result_dict, ensure_ascii=False, default=str)

        # Send tool results back to Claude
        messages.append({"role": "user", "content": tool_results})

        await asyncio.sleep(0.3)

    return f"Reached max iterations ({max_iterations}). Last response: {final_text}"
