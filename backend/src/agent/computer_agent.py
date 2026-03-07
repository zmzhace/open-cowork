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
2. 自己动手，无需用户参与：不要告诉用户"请手动打开"，你需要自己完成打开、定位、输入、发送的全过程。
3. 如果某个方法不工作，立刻换策略，不要在同一种失败方法上反复尝试。

## 🎯 核心哲学：怎么快怎么来，只要准确

你是一个 **实用主义 Agent**。不拘泥于某一种方法，哪种方式最快最准就用哪种。

### 黄金法则：
1. **速度优先，准确为王** — 能用命令行直接搞定的就不要绕弯路
2. **灵活切换** — 命令行、视觉点击、开始菜单搜索都是你的工具，按需使用
3. **最多 2 步没进展就换策略** — 一种方法不行就立刻换另一种

### 🚫 唯一禁止的事：
- ❌ 同一个失败的操作反复尝试 3 次以上
- ❌ 用 `exec` 反复运行 `where`、`dir /s`、`reg query` 全盘搜索（太慢）
- ❌ 不截图就声称任务完成

## 🚀 高效执行原则

1. **一次性规划多步操作** — 在一轮中调用多个工具
2. **并行执行独立操作** — 如果互不依赖，同一轮全部调用
3. **批量操作** — 需要多个信息时，一次性发起所有查询

### 可以并行的操作：
- 所有查询类操作：process(list), window(list), file(read), clipboard(read)
- screen(screenshot) 可以和 window(list)、process(list) 并行

### 必须串行的操作：
- GUI 操作：screen 工具的所有操作必须按顺序执行
- 写操作：file(write), exec(command) 等有副作用的操作

## 🛠️ 你的工具

- **screen** — 截屏、鼠标点击、键盘输入、等待
- **window** — 列出/聚焦/管理桌面窗口
- **process** — 查看/结束运行中的进程
- **exec** — 运行系统命令（可以用 `start 程序名` 快速启动程序！）
- **file** — 读写文件
- **clipboard** — 读写剪贴板
- **app_finder** — 搜索已安装的程序路径

## ⭐ 打开/激活程序的最佳实践

**选择最快的方式：**

### 方式 1：命令行直接启动（最快！推荐！）
```python
# 必须加 start 前缀才能非阻塞启动 GUI 程序
exec(command="start qq")
exec(command="start WeChat")
exec(command="start notepad")
exec(command="start chrome https://baidu.com")
```
> [!IMPORTANT]
> 启动 GUI 程序时务必使用 `start` 前缀，否则执行会阻塞直到程序被手动关闭。


### 方式 2：视觉点击（当命令行不好用时）
1. `screen(action="screenshot")` — 看一眼桌面
2. 看到目标图标 → 确认图标下方文字 → 双击

### 方式 3：开始菜单搜索（当前两种都不好用时）
1. `screen(action="press", text="win")` — 打开开始菜单
2. `screen(action="type", text="程序名")` — 搜索
3. `screen(action="press", text="enter")` — 回车打开

### 打开后验证：
- 不管用哪种方式打开，最后都要 `screen(action="screenshot")` 确认程序确实打开了
- 如果打开了错误的程序，诚实告知用户并修正

## 🛑 白屏处理（应对渲染延迟）

如果截图后发现目标窗口 **完全空白、全灰、全白**：
1. 不要放弃，这只是渲染延迟！
2. 调用 `screen(action="wait", amount=2)` 等待，然后重新截图
3. 如果仍然白屏，点击窗口中心强制重绘：`screen(action="click", x=中心, y=中心)`
4. 如果反复白屏（3次以上），尝试关闭窗口重新打开

## 使用 screen 工具的注意事项（坐标换算 — 极其重要！）

截图被缩放到了 **1280px 宽**。你在截图中看到的坐标是 **缩放后的坐标**，不能直接用于点击！

### 坐标换算公式：
```
实际点击 X = 截图中看到的 X × (screen_width / 1280)
实际点击 Y = 截图中看到的 Y × (screen_width / 1280)
```

### 举例：
- 截图工具返回 `screen_width: 2560`，缩放比例 = 2560 / 1280 = **2.0**
- 你在截图中看到 QQ 图标在 x=400, y=300（这是缩放后的坐标！）
- 实际点击坐标 = x=400×2.0=**800**, y=300×2.0=**600**
- 你应该调用 `screen(action="click", x=800, y=600)`

### 常见错误（绝对不要犯！）：
- ❌ 直接用截图中看到的坐标点击（会点偏！）
- ❌ 忘记乘以缩放比例
- ✅ 每次点击前都要把截图坐标 × 缩放比例

### 其他注意事项：
- screen 工具的多个 GUI 操作必须串行执行（一个接一个）
- 截图后仔细分析画面内容再决定下一步操作
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
                on_step(iteration + 1, f"Time limit reached ({max_time_seconds}s)")
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
        tool_calls = []
        final_text = ""

        for block in response.content:
            if hasattr(block, 'text') and block.text:
                final_text += block.text
                if on_step:
                    on_step(iteration + 1, f"[reply] {block.text[:100]}")

            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                if on_step:
                    on_step(iteration + 1, f"[tool] {block.name}({json.dumps(block.input, ensure_ascii=False)[:100]})")

        # If no tools were used, Claude is done
        if not tool_calls:
            if on_step:
                on_step(iteration + 1, "Done")
            return final_text

        # Execute tools (with parallel optimization)
        if on_step and len(tool_calls) > 1:
            on_step(iteration + 1, f"Executing {len(tool_calls)} tools (parallel where possible)...")
        
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
                    on_step(iteration + 1, "[warn] Loop detected!")
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
                        on_step(iteration + 1, "[warn] Alternating loop detected!")
                    if isinstance(tool_results[-1]["content"], str):
                        result_dict = json.loads(tool_results[-1]["content"])
                        result_dict["_system_warning"] = "检测到交替循环模式（A-B-A-B）。请尝试完全不同的方法！"
                        tool_results[-1]["content"] = json.dumps(result_dict, ensure_ascii=False, default=str)

        # Send tool results back to Claude
        messages.append({"role": "user", "content": tool_results})

        await asyncio.sleep(0.3)

    return f"Reached max iterations ({max_iterations}). Last response: {final_text}"
