# Computer Agent ReAct 流程分析

## 📋 概述

分析 `backend/src/agent/computer_agent.py` 中的 ReAct (Reasoning + Acting) 循环实现，识别潜在问题和改进方向。

---

## 🔴 严重问题

### 1. 截图处理的消息结构问题

**问题位置**: Line 175-189

```python
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
```

**问题分析**:
1. **破坏了 tool_result 的完整性**: 截图应该作为 tool_result 的一部分返回，而不是单独的消息
2. **违反了 Anthropic API 规范**: 在 tool_use 之后必须紧跟 tool_result，不能插入其他消息
3. **人为添加 assistant 消息**: `"我已收到截图，正在分析..."` 这条消息不是 LLM 生成的，会混淆对话历史
4. **可能导致 API 错误**: Anthropic API 对消息顺序有严格要求

**正确做法**:
```python
# 截图应该直接包含在 tool_result 中
if tool_name == "screen" and tool_input.get("action") == "screenshot":
    tool_results.append({
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result.pop("image_base64")
                }
            },
            {
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False)
            }
        ]
    })
else:
    tool_results.append({
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": json.dumps(result, ensure_ascii=False, default=str),
    })
```

### 2. 循环检测逻辑过于简单

**问题位置**: Line 157-167

```python
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
```

**问题**:
1. **只检测完全相同的操作**: 无法检测语义相似的循环（如反复点击相近坐标）
2. **窗口太小**: 只看最近 3 次操作，无法检测更长的循环模式（A→B→A→B）
3. **警告方式不当**: 修改 tool_result 内容可能导致 JSON 解析问题
4. **没有强制中断**: 只是警告，Agent 可能继续循环

**改进建议**:
```python
class LoopDetector:
    def __init__(self, window_size=10, threshold=3):
        self.actions = []
        self.window_size = window_size
        self.threshold = threshold
    
    def add_action(self, tool_name: str, tool_input: dict) -> tuple[bool, str]:
        """返回 (is_loop, warning_message)"""
        # 对坐标进行模糊匹配
        if tool_name == "screen" and "x" in tool_input:
            action_key = f"{tool_name}:{tool_input.get('action')}:~{tool_input['x']//50}~{tool_input['y']//50}"
        else:
            action_key = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
        
        self.actions.append(action_key)
        if len(self.actions) > self.window_size:
            self.actions.pop(0)
        
        # 检测完全重复
        if len(self.actions) >= self.threshold:
            if len(set(self.actions[-self.threshold:])) == 1:
                return True, f"检测到完全相同的操作重复 {self.threshold} 次"
        
        # 检测交替模式 (A-B-A-B)
        if len(self.actions) >= 4:
            if (self.actions[-1] == self.actions[-3] and 
                self.actions[-2] == self.actions[-4]):
                return True, "检测到交替循环模式"
        
        # 检测高频操作
        recent = self.actions[-6:] if len(self.actions) >= 6 else self.actions
        if len(recent) >= 4:
            most_common = max(set(recent), key=recent.count)
            if recent.count(most_common) >= 4:
                return True, f"操作 {most_common} 在最近 {len(recent)} 步中出现了 {recent.count(most_common)} 次"
        
        return False, ""
```

### 3. 错误处理不完整

**问题位置**: Line 107-113

```python
try:
    response = await client.messages.create(...)
except Exception as e:
    error_msg = str(e)
    if on_step:
        on_step(iteration + 1, f"API error: {error_msg[:100]}")
    return f"API Error: {error_msg}"
```

**问题**:
1. **捕获所有异常**: 过于宽泛，可能隐藏编程错误
2. **没有重试机制**: 网络抖动会直接失败
3. **没有保存状态**: 失败后无法恢复
4. **错误信息截断**: `[:100]` 可能丢失关键信息

**改进建议**:
```python
from anthropic import APIError, APIConnectionError, RateLimitError
import asyncio

async def call_llm_with_retry(client, max_retries=3, **kwargs):
    """带重试的 LLM 调用"""
    for attempt in range(max_retries):
        try:
            return await client.messages.create(**kwargs)
        
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 指数退避
            if on_step:
                on_step(iteration + 1, f"Rate limited, waiting {wait_time}s...")
            await asyncio.sleep(wait_time)
        
        except APIConnectionError as e:
            if attempt == max_retries - 1:
                raise
            if on_step:
                on_step(iteration + 1, f"Connection error, retrying...")
            await asyncio.sleep(1)
        
        except APIError as e:
            # 4xx 错误不重试
            if 400 <= e.status_code < 500:
                raise
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)
```

---

## 🟡 中等问题

### 4. 工具执行缺少异常处理

**问题位置**: Line 145-150

```python
# Execute the tool
tool_module = TOOLS.get(tool_name)
if tool_module:
    result = tool_module.execute(**tool_input)
else:
    result = {"error": f"Unknown tool: {tool_name}"}
```

**问题**:
1. **工具执行可能抛出异常**: 没有 try-catch
2. **同步执行**: 阻塞事件循环
3. **没有超时控制**: 工具可能卡死
4. **没有权限检查**: 任何工具都可以执行

**改进建议**:
```python
import asyncio
from functools import wraps

def async_tool_wrapper(sync_func):
    """将同步工具函数包装为异步"""
    @wraps(sync_func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: sync_func(*args, **kwargs))
    return wrapper

async def execute_tool_safely(tool_name: str, tool_input: dict, timeout: int = 30) -> dict:
    """安全执行工具，带超时和异常处理"""
    tool_module = TOOLS.get(tool_name)
    if not tool_module:
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        # 权限检查
        if not check_permission(tool_name, tool_input):
            return {"error": f"Permission denied for {tool_name}"}
        
        # 异步执行带超时
        execute_func = async_tool_wrapper(tool_module.execute)
        result = await asyncio.wait_for(
            execute_func(**tool_input),
            timeout=timeout
        )
        return result
    
    except asyncio.TimeoutError:
        return {"error": f"Tool {tool_name} timed out after {timeout}s"}
    
    except Exception as e:
        import traceback
        return {
            "error": f"Tool execution failed: {str(e)}",
            "traceback": traceback.format_exc()
        }
```

### 5. 消息历史管理问题

**问题**:
1. **无限增长**: messages 列表会越来越大，超过 token 限制
2. **没有摘要机制**: 长对话会丢失上下文
3. **没有持久化**: 进程重启后丢失历史

**改进建议**:
```python
class ConversationManager:
    def __init__(self, max_tokens=100000):
        self.messages = []
        self.max_tokens = max_tokens
        self.archived_summary = None
    
    def add_message(self, message: dict):
        self.messages.append(message)
        self._check_and_compress()
    
    def _estimate_tokens(self) -> int:
        """粗略估算 token 数量"""
        import json
        text = json.dumps(self.messages)
        return len(text) // 4  # 粗略估算
    
    async def _check_and_compress(self):
        """检查并压缩历史"""
        if self._estimate_tokens() > self.max_tokens * 0.8:
            # 保留最近的消息，压缩旧消息
            keep_recent = 10
            old_messages = self.messages[:-keep_recent]
            
            # 用 LLM 生成摘要
            summary = await self._summarize(old_messages)
            
            # 替换为摘要
            self.messages = [
                {"role": "user", "content": f"[之前的对话摘要]: {summary}"}
            ] + self.messages[-keep_recent:]
    
    async def _summarize(self, messages: list) -> str:
        """生成对话摘要"""
        # 实现摘要逻辑
        pass
```

### 6. 缺少状态管理

**问题**:
- 没有跟踪任务进度
- 无法暂停/恢复
- 无法查看中间状态

**改进建议**:
```python
from enum import Enum
from dataclasses import dataclass
from typing import List

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentState:
    task_id: str
    task: str
    status: TaskStatus
    current_iteration: int
    messages: List[dict]
    tool_results: List[dict]
    created_at: float
    updated_at: float
    
    def save(self):
        """保存到数据库或文件"""
        pass
    
    @classmethod
    def load(cls, task_id: str):
        """从存储加载"""
        pass
```

---

## 🟢 轻微问题

### 7. 硬编码的配置

**问题**:
- `max_tokens=4096` 硬编码
- `time.sleep(0.3)` 魔法数字
- 截图缩放到 1280px 固定值

**建议**: 使用配置类
```python
@dataclass
class AgentConfig:
    max_tokens: int = 4096
    max_iterations: int = 50
    tool_timeout: int = 30
    step_delay: float = 0.3
    screenshot_max_width: int = 1280
    loop_detection_window: int = 10
    loop_detection_threshold: int = 3
```

### 8. 日志不完整

**问题**:
- 只有 `on_step` 回调，没有结构化日志
- 无法追踪完整的执行流程
- 难以调试问题

**建议**:
```python
import logging
import json

logger = logging.getLogger(__name__)

# 在关键位置添加日志
logger.info(f"Starting task: {task}", extra={
    "task_id": task_id,
    "model": model,
    "max_iterations": max_iterations
})

logger.debug(f"Tool call: {tool_name}", extra={
    "tool_name": tool_name,
    "tool_input": tool_input,
    "iteration": iteration
})

logger.info(f"Tool result", extra={
    "tool_name": tool_name,
    "result_size": len(str(result)),
    "execution_time": elapsed
})
```

---

## 🎯 架构改进建议

### 1. 分离关注点

```python
class ReActAgent:
    def __init__(self, llm_client, tool_executor, config):
        self.llm = llm_client
        self.tools = tool_executor
        self.config = config
        self.conversation = ConversationManager()
        self.loop_detector = LoopDetector()
        self.state = AgentState()
    
    async def run(self, task: str) -> str:
        """主循环"""
        pass
    
    async def _think(self) -> Response:
        """调用 LLM 思考"""
        pass
    
    async def _act(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """执行工具"""
        pass
    
    def _should_continue(self) -> bool:
        """判断是否继续"""
        pass
```

### 2. 添加中间件系统

```python
class Middleware:
    async def before_llm_call(self, messages):
        pass
    
    async def after_llm_call(self, response):
        pass
    
    async def before_tool_call(self, tool_name, tool_input):
        pass
    
    async def after_tool_call(self, tool_name, result):
        pass

# 使用示例
agent.add_middleware(LoggingMiddleware())
agent.add_middleware(PermissionMiddleware())
agent.add_middleware(MetricsMiddleware())
```

### 3. 工具注册系统改进

```python
from typing import Protocol

class Tool(Protocol):
    name: str
    description: str
    schema: dict
    
    async def execute(self, **kwargs) -> dict:
        ...
    
    def validate_input(self, **kwargs) -> bool:
        ...
    
    def get_required_permissions(self) -> List[str]:
        ...

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        self._tools[tool.name] = tool
    
    def get_schemas(self) -> List[dict]:
        return [t.schema for t in self._tools.values()]
    
    async def execute(self, name: str, **kwargs) -> dict:
        tool = self._tools.get(name)
        if not tool:
            raise ToolNotFoundError(name)
        
        if not tool.validate_input(**kwargs):
            raise InvalidToolInputError(name, kwargs)
        
        return await tool.execute(**kwargs)
```

---

## 📊 性能优化建议

1. **并行工具执行**: 如果有多个独立的工具调用，可以并行执行
2. **缓存截图**: 避免重复截图
3. **流式响应**: 支持 streaming 模式，提升用户体验
4. **工具预热**: 提前加载常用工具

---

## 🔒 安全建议

1. **工具权限系统**: 不同工具需要不同权限
2. **输入验证**: 严格验证工具参数
3. **沙箱执行**: 危险操作在沙箱中执行
4. **审计日志**: 记录所有工具调用

---

## 📝 总结

### 最严重的问题（需要立即修复）:
1. ✅ 截图处理的消息结构违反 API 规范
2. ✅ 循环检测过于简单
3. ✅ 工具执行缺少异常处理

### 建议的修复顺序:
1. 修复截图在 tool_result 中的处理方式
2. 添加工具执行的异常处理和超时控制
3. 改进循环检测逻辑
4. 添加消息历史管理
5. 实现状态持久化
6. 添加完整的日志系统

这些改进将显著提升 Agent 的稳定性、可维护性和用户体验。
