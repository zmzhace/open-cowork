# Open-Cowork Design Document

**Date:** 2026-03-06
**Project:** Open-Cowork - WASM-Based Agentic Desktop Application
**Goal:** Create an open-source alternative to Claude's official Cowork feature

## Overview

Open-Cowork is a desktop application that brings agentic AI capabilities for knowledge work. It provides multi-step task execution, sub-agent coordination, file operations with permissions, document generation, computer use (application control, UI automation), and scheduled tasks - all running locally with strong security isolation.

## High-Level Architecture

### Three-Layer Design

**1. Frontend Layer (Electron + React)**
- Modern chat interface with streaming responses
- Task visualization dashboard (active tasks, sub-agents, progress)
- Settings panel (LLM provider config, API keys, permissions)
- File browser with permission controls
- Tool execution logs viewer

**2. Backend Layer (Python FastAPI)**
- Agent orchestrator (task decomposition, sub-agent coordination)
- LLM abstraction (unified interface for Claude + OpenAI-compatible APIs)
- Tool registry (file ops, document generation, web search, etc.)
- Session manager (conversation history, context)
- Scheduler service (cron-like scheduled tasks)
- IPC bridge (communicates with Electron via WebSocket/HTTP)

**3. Isolation Layer (WASM Runtime)**
- Wasmtime runtime embedded in Python backend
- Task executor (runs user tasks in WASM sandbox)
- WASI filesystem (controlled file access with permissions)
- Resource limits (CPU, memory, execution time)
- Security policies (network access, file permissions)

### Communication Flow

```
User → Electron UI → WebSocket → FastAPI Backend → LLM API
                                      ↓
                                Agent Orchestrator
                                      ↓
                                WASM Sandbox (Task Execution)
                                      ↓
                                File System (with permissions)
```

## Core Components

### 2.1 Frontend Components (Electron + React)

- **ChatInterface**: Main conversation view with markdown rendering, code highlighting, streaming message display
- **TaskDashboard**: Real-time view of active tasks, sub-agents, progress bars, execution logs
- **SettingsPanel**: LLM provider configuration (Claude API key, OpenAI-compatible endpoint URLs), permission settings, file access controls
- **FileExplorer**: Browse local files, set folder permissions, view file operations history
- **ToolViewer**: Display tool calls with inputs/outputs, execution time, success/failure status

### 2.2 Backend Components (Python FastAPI)

**AgentOrchestrator:**
- Decomposes complex tasks into subtasks
- Spawns and coordinates sub-agents
- Manages parallel execution
- Aggregates results from multiple agents

**LLMProvider (abstraction layer):**
- `ClaudeProvider`: Uses Anthropic SDK, supports streaming, tool use
- `OpenAIProvider`: Generic OpenAI-compatible client (works with Ollama, LM Studio, vLLM, etc.)
- Unified interface: `chat()`, `stream()`, `get_capabilities()`

**ToolRegistry:**
- File operations (read, write, delete, move, search)
- Document generation (DOCX, XLSX, PPTX via python-docx, openpyxl, python-pptx)
- Web search (DuckDuckGo API or similar)
- Code execution (in WASM sandbox)
- System commands (with permission checks)
- **Computer use tools:**
  - Screen capture and analysis (via PIL/Pillow, mss)
  - Mouse/keyboard control (via pyautogui, pynput)
  - Application launching and control (via subprocess, psutil)
  - UI element detection and interaction (via pyautogui, OCR)
  - Window management (focus, resize, move)

**WASMExecutor:**
- Embeds Wasmtime runtime
- Compiles Python tasks to WASM (via Pyodide)
- Enforces resource limits (CPU time, memory, file access)
- Provides WASI filesystem with permission model

**SessionManager:**
- SQLite database for persistence
- Stores conversation history, task state, file permissions
- Handles context window management

**Scheduler:**
- APScheduler for cron-like scheduling
- Persistent task queue
- Retry logic for failed tasks

### 2.3 Data Models

- **Task**: id, description, status, parent_task_id, assigned_agent, created_at, completed_at
- **Message**: id, session_id, role, content, tool_calls, timestamp
- **Permission**: path, access_level (read/write/execute), granted_at
- **ScheduledJob**: id, cron_expression, task_description, enabled, last_run
- **ComputerUsePermission**: action_type (screenshot/mouse/keyboard/app_launch), granted, scope (global/specific_app)

## Data Flow & Communication

### 3.1 User Task Execution Flow

```
1. User enters request in Electron UI
   ↓
2. Frontend sends message via WebSocket to FastAPI backend
   ↓
3. SessionManager stores message, retrieves conversation context
   ↓
4. AgentOrchestrator analyzes request:
   - Simple task → Direct LLM call
   - Complex task → Decompose into subtasks → Spawn sub-agents
   ↓
5. LLMProvider streams response:
   - Text chunks → Stream to frontend (real-time display)
   - Tool calls → Execute via ToolRegistry
   ↓
6. Tool execution (if needed):
   - File operations → Check permissions → Execute
   - Code execution → WASMExecutor → Run in sandbox
   - Document generation → Use Python libraries → Save to disk
   - Computer use → Check permissions → Execute in native Python (outside WASM)
   ↓
7. Results aggregated and streamed back to user
   ↓
8. SessionManager persists final state
```

### 3.2 Sub-Agent Coordination

When a complex task requires multiple sub-agents:
- Parent agent creates task plan with subtasks
- Each subtask assigned to a sub-agent (separate LLM conversation)
- Sub-agents execute in parallel where possible
- Parent agent monitors progress, aggregates results
- Shared context via SessionManager (sub-agents can access parent context)

### 3.3 WASM Sandbox Execution

```
Python Backend → WASMExecutor.execute(code, permissions)
                      ↓
                 Compile to WASM (Pyodide)
                      ↓
                 Wasmtime runtime loads module
                      ↓
                 Apply resource limits (CPU, memory, time)
                      ↓
                 Mount WASI filesystem (restricted paths)
                      ↓
                 Execute WASM module
                      ↓
                 Capture stdout/stderr/return value
                      ↓
                 Return results to backend
```

### 3.4 Streaming Response Protocol

WebSocket messages use JSON format:
```json
{
  "type": "message_chunk|tool_call|task_update|error",
  "session_id": "uuid",
  "content": "...",
  "metadata": {
    "agent_id": "main|sub-1|sub-2",
    "tool_name": "file_read",
    "progress": 0.5
  }
}
```

## Error Handling & Security

### 4.1 Error Handling Strategy

**LLM Provider Failures:**
- Retry logic with exponential backoff (3 attempts)
- Fallback to alternative provider if configured (e.g., Claude fails → try local Ollama)
- Graceful degradation (inform user, save context, allow manual retry)
- Rate limit handling (queue requests, show wait time to user)

**WASM Sandbox Errors:**
- Timeout enforcement (configurable, default 30s per task)
- Memory limit exceeded → Kill process, return error with resource usage stats
- Compilation failures → Return detailed error message, suggest fixes
- WASI permission denied → Show clear message about what access was blocked

**File Operation Errors:**
- Permission checks before execution (fail fast with clear message)
- Atomic operations where possible (write to temp file, then move)
- Rollback on failure (keep backup of modified files)
- User confirmation for destructive operations (delete, overwrite)

**Sub-Agent Coordination Errors:**
- Individual sub-agent failure doesn't crash parent
- Parent agent can retry failed subtasks
- Partial results returned if some sub-agents succeed
- Clear error attribution (which sub-agent failed, why)

**Computer Use Errors:**
- Permission denied → Show clear message about what action was blocked
- Application not found → Suggest alternatives or installation
- UI element not found → Return screenshot with error, allow retry
- Timeout on UI operations → Configurable timeout (default 10s per action)

### 4.2 Security Model

**Permission System:**
- Three levels: None, Read, Write (per directory/file)
- User grants permissions via UI before first access
- Permissions persisted in SQLite, can be revoked anytime
- WASM sandbox enforces permissions at WASI layer
- **Computer use permissions:**
  - Screenshot: Allow/Deny (can capture screen)
  - Mouse/Keyboard: Allow/Deny (can control input devices)
  - App Launch: Allow/Deny per application or global
  - Confirmation required for first use of each permission type

**API Key Security:**
- Keys stored in OS keychain (keyring library for Python)
- Never logged or displayed in UI
- Encrypted in transit (HTTPS for API calls)
- Option to use environment variables instead

**Sandbox Isolation:**
- WASM provides memory isolation
- No direct system calls (only through WASI)
- Network access controlled (can be disabled per task)
- No access to parent process memory

**Code Execution Safety:**
- All user-provided code runs in WASM sandbox
- Resource limits prevent DoS (CPU, memory, time)
- File system access restricted to approved paths
- No shell command execution without explicit permission

**Computer Use Safety:**
- All computer use actions run in native Python (outside WASM for OS access)
- Explicit permission required before first use
- Rate limiting on mouse/keyboard actions (prevent spam)
- Screenshot data analyzed by LLM before taking actions
- User can pause/stop automation at any time via UI
- Audit log of all computer use actions

### 4.3 Logging & Debugging

- Structured logging (JSON format) to `~/.open-cowork/logs/`
- Log levels: DEBUG, INFO, WARNING, ERROR
- Separate logs for: backend, WASM executor, LLM calls, tool execution
- UI shows real-time logs in developer console
- Privacy mode (disable logging of message content)

## Testing Strategy

### 5.1 Unit Tests

**Backend (Python + pytest):**
- `test_llm_providers.py`: Test Claude and OpenAI provider implementations, mock API responses, verify streaming
- `test_agent_orchestrator.py`: Test task decomposition, sub-agent spawning, result aggregation
- `test_wasm_executor.py`: Test WASM compilation, execution, resource limits, permission enforcement
- `test_tool_registry.py`: Test each tool (file ops, document generation, etc.)
- `test_session_manager.py`: Test persistence, context management, history retrieval

**Frontend (Jest + React Testing Library):**
- `ChatInterface.test.tsx`: Test message rendering, streaming display, user input
- `TaskDashboard.test.tsx`: Test task list, progress updates, sub-agent visualization
- `SettingsPanel.test.tsx`: Test configuration changes, API key validation
- `FileExplorer.test.tsx`: Test file browsing, permission granting

### 5.2 Integration Tests

- **End-to-end flow**: User request → LLM response → tool execution → result display
- **Sub-agent coordination**: Complex task with multiple sub-agents running in parallel
- **WASM sandbox**: Execute Python code in sandbox, verify isolation and permissions
- **File operations**: Read/write files with permission checks, verify rollback on error
- **Scheduled tasks**: Create scheduled job, verify execution at correct time
- **Computer use**: Take screenshot, analyze UI, click button, verify action executed correctly

### 5.3 Security Tests

- **Sandbox escape attempts**: Try to access files outside permitted paths, verify blocked
- **Resource exhaustion**: Infinite loops, memory bombs, verify limits enforced
- **Permission bypass**: Attempt operations without granted permissions, verify denied
- **API key leakage**: Verify keys never logged or exposed in UI
- **Computer use abuse**: Attempt rapid-fire clicks, verify rate limiting works

### 5.4 Performance Tests

- **Streaming latency**: Measure time from LLM token to UI display (target <100ms)
- **WASM startup time**: Measure sandbox initialization (target <500ms)
- **Concurrent sub-agents**: Test 5+ sub-agents running simultaneously
- **Large file operations**: Test with 100MB+ files, verify memory efficiency

### 5.5 Manual Testing Checklist

- [ ] Install on fresh macOS/Windows/Linux systems
- [ ] Configure Claude API and local Ollama
- [ ] Execute simple task (e.g., "create a todo list")
- [ ] Execute complex task requiring sub-agents (e.g., "analyze these 10 PDFs and create summary report")
- [ ] Test file permissions (grant, revoke, verify enforcement)
- [ ] Test scheduled tasks (create, edit, delete, verify execution)
- [ ] Test error scenarios (API failure, timeout, permission denied)
- [ ] Verify logs are written correctly
- [ ] Test computer use: "Take a screenshot and describe what you see"
- [ ] Test computer use: "Open Calculator app and compute 123 * 456"
- [ ] Test computer use: "Fill out this form in my browser"

## Technology Stack

**Frontend:**
- Electron (desktop framework)
- React (UI library)
- TypeScript (type safety)
- WebSocket (real-time communication)
- TailwindCSS (styling)

**Backend:**
- Python 3.11+
- FastAPI (async web framework)
- Anthropic SDK (Claude API)
- OpenAI Python client (OpenAI-compatible APIs)
- Wasmtime-py (WASM runtime)
- SQLite (persistence)
- APScheduler (task scheduling)
- python-docx, openpyxl, python-pptx (document generation)
- keyring (secure key storage)
- **Computer use libraries:**
  - pyautogui (mouse/keyboard control)
  - pynput (input monitoring)
  - mss (fast screenshot capture)
  - Pillow/PIL (image processing)
  - pytesseract (OCR for UI element detection)
  - psutil (process management)

**Development:**
- pytest (Python testing)
- Jest + React Testing Library (frontend testing)
- ESLint + Prettier (code quality)
- Black + isort (Python formatting)

## Next Steps

1. Create detailed implementation plan (via writing-plans skill)
2. Set up project structure and dependencies
3. Implement core backend components
4. Build frontend UI
5. Integrate WASM sandbox
6. Add testing infrastructure
7. Package for distribution (macOS, Windows, Linux)
