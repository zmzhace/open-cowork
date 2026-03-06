# Open-Cowork Architecture

## Overview

Open-Cowork is a desktop application that provides agentic capabilities similar to Claude Code. It consists of three main layers:

1. **Frontend Layer** - Electron + React UI
2. **Backend Layer** - FastAPI server with agent orchestration
3. **Tool Layer** - Extensible tool system for various operations

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Electron)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   React UI  │  │  IPC Bridge  │  │  Main Process │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────┴────────────────────────────────┐
│                  Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │            Agent Manager                         │   │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────┐ │   │
│  │  │ LLM Router │  │ Tool Router │  │ History  │ │   │
│  │  └────────────┘  └─────────────┘  └──────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ LLM Provider │  │ Tool Registry│  │  Permission  │  │
│  │  Abstraction │  │              │  │   Manager    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                    Tool Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │   File   │  │ Computer │  │ Document │  │  Custom ││
│  │   Tools  │  │   Use    │  │   Gen    │  │  Tools  ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└──────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend Layer

#### Electron Main Process (`frontend/main.js`)
- Window management
- IPC communication setup
- System integration

#### React UI (`frontend/src/`)
- Chat interface
- Message display
- User input handling
- Real-time updates

#### Preload Script (`frontend/preload.js`)
- Secure IPC bridge
- Context isolation
- API exposure to renderer

### Backend Layer

#### FastAPI Application (`backend/src/main.py`)
- REST API endpoints
- CORS configuration
- Database initialization
- Route registration

#### Agent Manager (`backend/src/agent_manager.py`)
- Task execution orchestration
- Conversation history management
- Tool call routing
- LLM interaction coordination

#### LLM Providers (`backend/src/llm/`)

**Base Interface** (`base.py`)
```python
class LLMProvider(ABC):
    async def chat(messages, tools) -> LLMResponse
    async def stream(messages, tools) -> AsyncIterator[str]
    def get_capabilities() -> Dict
```

**Implementations:**
- `ClaudeProvider` - Anthropic Claude API
- `OpenAIProvider` - OpenAI-compatible APIs (Ollama, LM Studio, vLLM)

#### Tool System (`backend/src/tools/`)

**Base Tool** (`base.py`)
```python
class Tool(ABC):
    name: str
    description: str
    parameters: Dict

    async def execute(**kwargs) -> Any
    def to_dict() -> Dict  # For LLM
```

**Tool Registry** (`registry.py`)
- Tool registration
- Tool lookup
- LLM format conversion

**Available Tools:**
- `FileReadTool` - Read file contents
- `FileWriteTool` - Write to files
- `ScreenshotTool` - Capture screenshots
- `MouseMoveTool` - Move mouse cursor
- `MouseClickTool` - Click mouse buttons
- `KeyboardTypeTool` - Type text

#### Permission System (`backend/src/permissions.py`)
- Path-based access control
- Operation authorization (read/write/execute)
- Permission granting/revoking

#### Database Layer (`backend/src/`)

**Models** (`models.py`)
- `Task` - Task tracking
- `Message` - Conversation history
- `Permission` - Access control
- `ScheduledJob` - Scheduled tasks
- `ComputerUsePermission` - Computer use authorization

**Database** (`database.py`)
- SQLAlchemy configuration
- Session management
- Connection pooling

## Data Flow

### Task Execution Flow

```
1. User Input (Frontend)
   ↓
2. HTTP Request to Backend
   ↓
3. Agent Manager receives task
   ↓
4. Agent Manager calls LLM Provider
   ↓
5. LLM returns response with tool calls
   ↓
6. Agent Manager executes tools via Tool Registry
   ↓
7. Tool results added to conversation
   ↓
8. Agent Manager calls LLM again if needed
   ↓
9. Final response sent to Frontend
   ↓
10. UI updates with response
```

### Tool Execution Flow

```
1. LLM requests tool use
   ↓
2. Agent Manager validates tool exists
   ↓
3. Permission Manager checks authorization
   ↓
4. Tool.execute() called with parameters
   ↓
5. Tool performs operation
   ↓
6. Result returned to Agent Manager
   ↓
7. Result added to conversation context
```

## Security Considerations

### Permission System
- All file operations require explicit permission
- Computer use tools require authorization
- Path-based access control

### Sandboxing (Planned)
- WASM-based tool execution
- Resource limits
- Network isolation

### API Security
- CORS configuration
- Input validation
- Rate limiting (planned)

## Extensibility

### Adding New LLM Providers

1. Implement `LLMProvider` interface
2. Add provider-specific configuration
3. Register in provider factory

```python
class CustomProvider(LLMProvider):
    async def chat(self, messages, tools=None, **kwargs):
        # Implementation
        pass
```

### Adding New Tools

1. Extend `Tool` base class
2. Implement `execute()` method
3. Register with `ToolRegistry`

```python
class CustomTool(Tool):
    name = "custom_tool"
    description = "Does something custom"

    async def execute(self, **kwargs):
        # Implementation
        return result
```

## Performance Considerations

- Async/await throughout for non-blocking I/O
- Connection pooling for database
- Streaming responses for large outputs
- Lazy loading of tools

## Future Enhancements

1. **WebSocket Support** - Real-time bidirectional communication
2. **Plugin System** - Dynamic tool loading
3. **Multi-Agent Coordination** - Agent-to-agent communication
4. **WASM Sandbox** - Secure tool execution
5. **Cloud Deployment** - Scalable backend infrastructure
