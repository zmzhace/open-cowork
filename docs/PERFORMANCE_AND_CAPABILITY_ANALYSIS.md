# Computer Agent 性能与能力发挥深度分析

## 🎯 核心问题：没有充分发挥 Claude Sonnet 的智能

---

## 🔴 最严重的性能问题

### 1. **单步执行模式 - 严重限制并行能力**

**问题核心**: 当前实现是严格的单步 ReAct 循环：
```
思考 → 执行1个工具 → 等待结果 → 思考 → 执行1个工具 → ...
```

**Claude Sonnet 的真实能力**: 
- 可以在一次响应中调用**多个工具**
- 可以并行规划多个独立操作
- 具有强大的任务分解和并行思维能力

**当前代码的限制**:
```python
for block in response.content:
    if block.type == "tool_use":
        # 执行工具
        result = tool_module.execute(**tool_input)
        # 立即添加到 tool_results
```

这段代码**支持多工具调用**，但是：

1. **工具是串行执行的** - 即使 Claude 返回多个工具调用，也是一个接一个执行
2. **没有利用并行性** - 独立的工具调用（如同时查询多个进程）可以并行执行
3. **每次只能规划一步** - System Prompt 说"每次只做一个逻辑步骤"，人为限制了 Claude 的规划能力

**性能影响**:
- 完成一个复杂任务需要 10-20 轮对话
- 每轮都有网络延迟（API 调用）
- 总耗时 = 轮数 × (API延迟 + 工具执行时间)

**改进方案**:

```python
# 1. 并行执行独立工具
import asyncio

async def execute_tools_parallel(tool_calls: List[ToolCall]) -> List[ToolResult]:
    """并行执行可以并行的工具"""
    # 分析依赖关系
    independent_groups = analyze_dependencies(tool_calls)
    
    results = []
    for group in independent_groups:
        # 每组内的工具可以并行执行
        group_results = await asyncio.gather(*[
            execute_tool_async(call) for call in group
        ])
        results.extend(group_results)
    
    return results

def analyze_dependencies(tool_calls: List[ToolCall]) -> List[List[ToolCall]]:
    """分析工具调用的依赖关系，返回可并行执行的分组"""
    # 简单规则：
    # - 所有读操作可以并行
    # - 写操作必须串行
    # - screen 操作必须串行（GUI 操作有顺序）
    
    read_tools = ["process", "window", "file(read)", "clipboard(read)"]
    write_tools = ["file(write)", "clipboard(write)", "exec"]
    sequential_tools = ["screen"]
    
    groups = []
    current_parallel_group = []
    
    for call in tool_calls:
        if call.name in sequential_tools or call.name in write_tools:
            # 先执行之前的并行组
            if current_parallel_group:
                groups.append(current_parallel_group)
                current_parallel_group = []
            # 写操作单独一组
            groups.append([call])
        else:
            # 读操作可以并行
            current_parallel_group.append(call)
    
    if current_parallel_group:
        groups.append(current_parallel_group)
    
    return groups
```

**更重要的是修改 System Prompt**:

```python
SYSTEM_PROMPT = """你是一个智能计算机操控助手，运行在 Windows 系统上。

## 🚀 高效执行原则（重要！）

你具有强大的并行思维和任务规划能力。请充分利用：

1. **一次性规划多步操作** - 不要每次只做一个操作，而是分析任务，一次性调用多个工具
2. **并行执行独立操作** - 如果多个操作互不依赖，可以在同一轮中全部调用
3. **批量查询** - 需要多个信息时，一次性发起所有查询

### 示例：打开微信并发送消息

❌ 低效方式（需要 5 轮对话）：
- 第1轮：process(list, filter="WeChat")
- 第2轮：window(list)  
- 第3轮：window(focus, title="微信")
- 第4轮：screen(screenshot)
- 第5轮：screen(click, ...)

✅ 高效方式（2-3 轮对话）：
- 第1轮：同时调用 process(list, filter="WeChat") + window(list)
- 第2轮：window(focus) + screen(screenshot)
- 第3轮：根据截图执行操作

### 可以并行的操作类型：
- 查询类：process(list), window(list), file(read), clipboard(read)
- 多个独立的信息收集操作

### 必须串行的操作：
- GUI 操作：screen 工具的所有操作必须按顺序执行
- 写操作：file(write), exec(command) 等有副作用的操作
- 有依赖关系的操作：后续操作依赖前面的结果

## 你的工具
...（保持原有工具说明）

## 任务规划策略

在开始执行前，先在脑海中规划：
1. 这个任务可以分解为哪几个步骤？
2. 哪些步骤可以并行执行？
3. 哪些步骤必须等待前面的结果？

然后一次性调用所有可以并行的工具，而不是一个一个来。
"""
```

### 2. **截图处理效率低下**

**问题**:
```python
# 截图被单独发送，需要额外一轮对话
if pending_screenshots:
    messages.append({"role": "assistant", "content": "我已收到截图，正在分析..."})
    messages.append({"role": "user", "content": screenshot_content})
```

**性能影响**:
- 每次截图都增加一轮 API 调用
- 如果任务需要 5 次截图，就多了 5 轮对话
- 每轮增加 1-3 秒延迟

**正确做法**:
```python
# 截图应该直接在 tool_result 中返回
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
```

**性能提升**: 
- 减少 30-50% 的 API 调用次数
- 任务完成时间减少 20-40%

### 3. **缺少思维链（Chain of Thought）优化**

**问题**: System Prompt 没有引导 Claude 进行深度思考和规划

**Claude Sonnet 的优势**:
- 强大的推理能力
- 可以进行复杂的任务分解
- 能够预见潜在问题并提前规划

**当前限制**: Prompt 过于简单，没有激发这些能力

**改进方案**:

```python
SYSTEM_PROMPT = """你是一个智能计算机操控助手。

## 🧠 思考框架

在执行任务前，请使用以下思考框架（在 text 块中表达你的思考）：

### 1. 任务理解
- 用户的最终目标是什么？
- 有哪些隐含的需求？
- 可能遇到什么问题？

### 2. 策略规划
- 将任务分解为 3-5 个主要步骤
- 识别哪些步骤可以并行
- 预判每个步骤可能的失败点

### 3. 执行计划
- 第一批要调用哪些工具？（尽可能多）
- 如果失败，备选方案是什么？
- 如何验证每步是否成功？

### 示例思考过程：

任务："打开微信并给张三发送'你好'"

我的思考：
1. 任务分解：
   - 确认微信是否运行
   - 激活微信窗口
   - 找到张三的聊天
   - 发送消息

2. 并行机会：
   - 可以同时查询进程和窗口列表
   - 激活窗口后立即截图，不用等待

3. 潜在问题：
   - 微信可能在托盘中隐藏
   - 可能需要登录
   - 张三可能不在最近联系人

4. 执行：
   - 第一批：process(list) + window(list) 并行查询
   - 第二批：根据结果决定 focus 还是 exec
   - 第三批：screenshot 确认界面
   - 后续：根据截图内容操作

现在开始执行...
"""
```

### 4. **没有利用 Claude 的视觉理解能力**

**问题**: 截图后只是简单地让 Claude "分析屏幕内容"

**Claude Sonnet 的视觉能力**:
- 可以识别 UI 元素的语义（按钮、输入框、菜单）
- 可以理解界面布局和层次结构
- 可以推断用户意图和下一步操作

**当前限制**: 没有引导 Claude 充分利用视觉信息

**改进方案**:

```python
# 在 screen tool 的返回中添加引导
def execute(action: str, ...):
    if action == "screenshot":
        return {
            "type": "screenshot",
            "image_base64": img_b64,
            "screen_width": w,
            "screen_height": h,
            "analysis_guide": """
请详细分析这张截图：
1. 识别所有可交互元素（按钮、输入框、链接等）及其大致坐标
2. 判断当前界面的状态（正常/加载中/错误/空白）
3. 找出与任务相关的关键元素
4. 规划下一步操作的精确坐标

注意：
- 坐标需要按缩放比例换算
- 如果界面异常（白屏、卡死），说明原因并提出备选方案
- 如果找不到目标元素，考虑是否需要滚动或切换标签页
            """
        }
```

### 5. **工具粒度过粗，限制了智能决策**

**问题**: 某些工具功能过于简单，Claude 需要多次调用才能完成一个逻辑操作

**示例**: 
```python
# 当前：需要 3 次工具调用
1. process(list, filter="WeChat")  # 查询进程
2. window(list)                     # 查询窗口
3. window(focus, title="微信")      # 激活窗口

# 优化：提供高级工具
1. app_manager(action="ensure_running", app="WeChat", focus=True)
   # 一次调用完成：检查→启动（如需要）→激活
```

**改进方案**: 添加高级工具

```python
# 新增高级工具
TOOL_SCHEMA = {
    "name": "app_manager",
    "description": "高级应用管理：确保应用运行并激活，自动处理各种情况",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["ensure_running", "restart", "close_all"],
            },
            "app_name": {"type": "string", "description": "应用名称（如 WeChat, Chrome）"},
            "focus": {"type": "boolean", "description": "是否激活窗口", "default": True},
            "wait_ready": {"type": "boolean", "description": "是否等待应用完全加载", "default": True},
        },
        "required": ["action", "app_name"],
    },
}

def execute(action: str, app_name: str, focus: bool = True, wait_ready: bool = True):
    """智能应用管理"""
    if action == "ensure_running":
        # 1. 检查进程
        processes = check_process(app_name)
        
        if not processes:
            # 2. 未运行，查找并启动
            app_path = find_app_path(app_name)
            if app_path:
                launch_app(app_path)
                time.sleep(2)  # 等待启动
            else:
                return {"error": f"找不到应用: {app_name}"}
        
        # 3. 激活窗口
        if focus:
            windows = find_windows(app_name)
            if windows:
                activate_window(windows[0])
                
                # 4. 等待就绪
                if wait_ready:
                    wait_for_window_ready(windows[0])
                
                return {
                    "status": "ready",
                    "was_running": bool(processes),
                    "window": windows[0]
                }
        
        return {"status": "running", "was_running": bool(processes)}
```

---

## 🟡 中等性能问题

### 6. **缺少上下文缓存**

**问题**: 每次 API 调用都发送完整的对话历史

**Claude 的 Prompt Caching 功能**:
- 可以缓存 System Prompt 和历史消息
- 减少 token 消耗和延迟
- 特别适合长对话场景

**改进方案**:

```python
# 使用 Prompt Caching
response = await client.messages.create(
    model=model,
    max_tokens=4096,
    system=[
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}  # 缓存 system prompt
        }
    ],
    messages=messages,
    tools=TOOL_SCHEMAS,
)

# 对于长对话，缓存早期消息
if len(messages) > 10:
    # 标记前 N 条消息为可缓存
    for i in range(len(messages) - 5):
        if isinstance(messages[i]["content"], list):
            messages[i]["content"][-1]["cache_control"] = {"type": "ephemeral"}
```

**性能提升**:
- 减少 50-80% 的输入 token 成本
- 减少 10-30% 的延迟

### 7. **没有使用流式响应**

**问题**: 等待完整响应才开始处理

**流式响应的优势**:
- 更快的首字节时间
- 可以边接收边执行工具
- 更好的用户体验

**改进方案**:

```python
async def run_agent_streaming(task: str, ...):
    """流式版本的 agent"""
    
    async with client.messages.stream(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=TOOL_SCHEMAS,
    ) as stream:
        
        current_tool_calls = []
        
        async for event in stream:
            if event.type == "content_block_start":
                if event.content_block.type == "tool_use":
                    # 开始收集工具调用
                    current_tool_calls.append({
                        "id": event.content_block.id,
                        "name": event.content_block.name,
                        "input": {}
                    })
            
            elif event.type == "content_block_delta":
                if event.delta.type == "tool_use":
                    # 累积工具参数
                    current_tool_calls[-1]["input"].update(event.delta.input)
            
            elif event.type == "content_block_stop":
                # 工具参数接收完整，可以立即开始执行
                if current_tool_calls and is_complete(current_tool_calls[-1]):
                    # 不等待所有工具调用，立即执行已完整的
                    asyncio.create_task(
                        execute_tool_async(current_tool_calls[-1])
                    )
```

### 8. **工具执行的同步阻塞**

**问题**: 
```python
result = tool_module.execute(**tool_input)  # 同步调用，阻塞事件循环
```

**影响**:
- 工具执行时无法处理其他任务
- 长时间操作（如启动应用）会阻塞整个 agent
- 无法实现真正的并行执行

**改进方案**:

```python
# 1. 将所有工具改为异步
async def execute(action: str, ...):
    if action == "screenshot":
        # 在线程池中执行 CPU 密集型操作
        loop = asyncio.get_event_loop()
        img_b64 = await loop.run_in_executor(None, _take_screenshot)
        return {...}
    
    elif action == "click":
        # GUI 操作也在线程池中执行
        await loop.run_in_executor(None, pyautogui.click, x, y)
        return {...}

# 2. 并行执行多个工具
async def execute_tools_batch(tool_calls: List[ToolCall]):
    """批量并行执行工具"""
    tasks = []
    for call in tool_calls:
        tool = TOOLS[call.name]
        task = tool.execute(**call.input)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理异常
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            results[i] = {"error": str(result)}
    
    return results
```

---

## 🟢 智能优化建议

### 9. **添加任务规划阶段**

**概念**: 在执行前，让 Claude 先做一次完整的任务规划

```python
async def run_agent_with_planning(task: str, ...):
    """带规划阶段的 agent"""
    
    # 第一阶段：规划
    planning_prompt = f"""
任务：{task}

请先不要执行任何工具，而是制定一个详细的执行计划：

1. 任务分析：
   - 最终目标是什么？
   - 需要哪些前置条件？
   - 可能遇到什么问题？

2. 步骤分解：
   - 列出 3-7 个主要步骤
   - 标注哪些步骤可以并行
   - 标注哪些步骤有依赖关系

3. 工具选择：
   - 每个步骤需要哪些工具？
   - 是否有更高效的工具组合？

4. 风险预案：
   - 每个步骤可能失败的原因
   - 备选方案是什么？

请以结构化的方式输出你的计划。
"""
    
    plan_response = await client.messages.create(
        model=model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": planning_prompt}],
    )
    
    plan = extract_plan(plan_response)
    
    # 第二阶段：执行
    execution_prompt = f"""
你已经制定了以下计划：
{plan}

现在开始执行这个计划。记住：
- 尽可能并行执行独立的步骤
- 每完成一个阶段，简要总结进度
- 如果遇到问题，参考你的备选方案
"""
    
    messages = [{"role": "user", "content": execution_prompt}]
    
    # 执行循环（同之前）
    ...
```

### 10. **自适应策略调整**

**概念**: 根据任务类型和执行情况，动态调整策略

```python
class AdaptiveAgent:
    def __init__(self):
        self.task_history = []
        self.success_patterns = {}
    
    async def run(self, task: str):
        # 分析任务类型
        task_type = self.classify_task(task)
        
        # 选择最佳策略
        strategy = self.select_strategy(task_type)
        
        # 执行
        result = await self.execute_with_strategy(task, strategy)
        
        # 学习
        self.learn_from_execution(task_type, strategy, result)
        
        return result
    
    def classify_task(self, task: str) -> str:
        """分类任务类型"""
        if "打开" in task or "启动" in task:
            return "app_launch"
        elif "发送" in task or "消息" in task:
            return "messaging"
        elif "查找" in task or "搜索" in task:
            return "search"
        else:
            return "general"
    
    def select_strategy(self, task_type: str) -> dict:
        """选择执行策略"""
        strategies = {
            "app_launch": {
                "max_parallel": 2,
                "prefer_tools": ["app_manager", "window"],
                "screenshot_timing": "after_action"
            },
            "messaging": {
                "max_parallel": 1,  # GUI 操作必须串行
                "prefer_tools": ["screen", "clipboard"],
                "screenshot_timing": "before_and_after"
            },
            "search": {
                "max_parallel": 5,
                "prefer_tools": ["file", "exec"],
                "screenshot_timing": "minimal"
            }
        }
        return strategies.get(task_type, strategies["general"])
```

### 11. **工具结果的智能摘要**

**问题**: 某些工具返回大量数据，浪费 token

**示例**:
```python
# window(list) 可能返回 50+ 个窗口
# process(list) 可能返回 100+ 个进程
```

**改进方案**:

```python
def summarize_tool_result(tool_name: str, result: dict, context: str) -> dict:
    """根据上下文智能摘要工具结果"""
    
    if tool_name == "window" and "windows" in result:
        # 只保留相关窗口
        relevant = filter_relevant_windows(result["windows"], context)
        return {
            "relevant_windows": relevant[:10],
            "total_count": len(result["windows"]),
            "note": f"显示最相关的 {len(relevant)} 个窗口（共 {len(result['windows'])} 个）"
        }
    
    elif tool_name == "process" and "processes" in result:
        # 只保留相关进程
        relevant = filter_relevant_processes(result["processes"], context)
        return {
            "relevant_processes": relevant[:20],
            "total_count": len(result["processes"]),
        }
    
    return result

def filter_relevant_windows(windows: list, context: str) -> list:
    """过滤相关窗口"""
    # 使用简单的关键词匹配
    keywords = extract_keywords(context)
    
    scored = []
    for window in windows:
        score = 0
        title_lower = window["title"].lower()
        for keyword in keywords:
            if keyword in title_lower:
                score += 1
        if score > 0:
            scored.append((score, window))
    
    scored.sort(reverse=True, key=lambda x: x[0])
    return [w for _, w in scored]
```

---

## 📊 性能对比预估

### 当前实现：
```
任务："打开微信并给张三发送'你好'"

第1轮：思考 → process(list)
第2轮：思考 → window(list)
第3轮：思考 → window(focus)
第4轮：思考 → screen(screenshot)
第5轮：分析截图
第6轮：思考 → screen(click, 搜索框)
第7轮：思考 → screen(type, "张三")
第8轮：思考 → screen(screenshot)
第9轮：分析截图
第10轮：思考 → screen(click, 聊天)
第11轮：思考 → screen(type, "你好")
第12轮：思考 → screen(click, 发送)

总计：12 轮对话
耗时：约 24-36 秒（假设每轮 2-3 秒）
```

### 优化后实现：
```
任务："打开微信并给张三发送'你好'"

第1轮：规划 + 并行执行 process(list) + window(list)
第2轮：app_manager(ensure_running, "WeChat") + screen(screenshot)
第3轮：分析截图 + 批量执行 [
    screen(click, 搜索框),
    screen(type, "张三"),
    screen(press, "enter")
]
第4轮：screen(screenshot) + 分析
第5轮：批量执行 [
    screen(type, "你好"),
    screen(click, 发送按钮)
]

总计：5 轮对话
耗时：约 10-15 秒
性能提升：60-70%
```

---

## 🎯 立即可实施的优化（按优先级）

### 优先级 1（立即实施）:
1. ✅ 修复截图在 tool_result 中的处理
2. ✅ 修改 System Prompt，鼓励并行思维
3. ✅ 实现工具的异步执行

### 优先级 2（本周完成）:
4. ✅ 实现工具并行执行
5. ✅ 添加高级工具（app_manager）
6. ✅ 启用 Prompt Caching

### 优先级 3（下周完成）:
7. ✅ 实现流式响应
8. ✅ 添加任务规划阶段
9. ✅ 工具结果智能摘要

---

## 💡 总结

当前实现的最大问题是：**人为限制了 Claude Sonnet 的智能**

- ❌ 强制单步执行
- ❌ 没有鼓励并行思维
- ❌ 工具粒度过细
- ❌ 缺少规划阶段
- ❌ 截图处理低效

通过上述优化，可以：
- ⚡ 减少 50-70% 的对话轮数
- ⚡ 提升 60-80% 的执行速度
- 🧠 充分发挥 Claude 的推理和规划能力
- 💰 减少 30-50% 的 API 成本

**核心理念**: 让 Claude 像人类专家一样思考和工作 - 先规划，再并行执行，而不是机械地一步一步来。
