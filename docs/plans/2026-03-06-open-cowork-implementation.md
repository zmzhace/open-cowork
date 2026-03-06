# Open-Cowork Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a WASM-based agentic desktop application that provides Claude Cowork-like capabilities with computer use, file operations, and multi-agent coordination.

**Architecture:** Electron frontend + Python FastAPI backend + WASM isolation layer. LLM abstraction supports Claude API and OpenAI-compatible endpoints. Computer use tools run in native Python with permission system.

**Tech Stack:** Electron, React, TypeScript, Python 3.11+, FastAPI, Wasmtime, SQLite, pyautogui, Anthropic SDK

---

## Phase 1: Project Foundation & Backend Core

### Task 1: Initialize Project Structure

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/src/__init__.py`
- Create: `frontend/package.json`
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Create project directories**

Run: `mkdir -p backend/src backend/tests frontend/src docs`

**Step 2: Create .gitignore**

Create `.gitignore`:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log
yarn-error.log
.DS_Store

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Environment
.env
.env.local

# Build
frontend/dist/
frontend/build/
```

**Step 3: Create backend requirements.txt**

Create `backend/requirements.txt`:
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
anthropic==0.18.0
openai==1.12.0
wasmtime==17.0.0
sqlalchemy==2.0.25
aiosqlite==0.19.0
apscheduler==3.10.4
python-docx==1.1.0
openpyxl==3.1.2
python-pptx==0.6.23
keyring==24.3.0
pyautogui==0.9.54
pynput==1.7.6
mss==9.0.1
pillow==10.2.0
pytesseract==0.3.10
psutil==5.9.8
websockets==12.0
pydantic==2.6.0
pytest==8.0.0
pytest-asyncio==0.23.4
black==24.1.1
isort==5.13.2
```

**Step 4: Create frontend package.json**

Create `frontend/package.json`:
```json
{
  "name": "open-cowork-frontend",
  "version": "0.1.0",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "electron": "^28.2.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.11"
  }
}
```

**Step 5: Create README.md**

Create `README.md`:
```markdown
# Open-Cowork

Open-source agentic desktop application with Claude Cowork-like capabilities.

## Features

- Multi-step task execution
- Sub-agent coordination
- File operations with permissions
- Computer use (screenshot, mouse/keyboard control, app launching)
- Document generation (DOCX, XLSX, PPTX)
- WASM sandbox isolation
- Claude API + OpenAI-compatible LLM support

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## Running

### Backend
```bash
cd backend
uvicorn src.main:app --reload
```

### Frontend
```bash
cd frontend
npm start
```

## License

MIT
```

**Step 6: Commit**

```bash
git add .gitignore README.md backend/requirements.txt frontend/package.json
git commit -m "feat: initialize project structure

- Add .gitignore for Python and Node
- Add backend requirements.txt with all dependencies
- Add frontend package.json with Electron + React
- Add README with setup instructions"
```

---

### Task 2: Setup Database Models

**Files:**
- Create: `backend/src/models.py`
- Create: `backend/src/database.py`
- Create: `backend/tests/test_models.py`

**Step 1: Write failing test for database setup**

Create `backend/tests/test_models.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, get_db
from src.models import Task, Message, Permission, ScheduledJob, ComputerUsePermission


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_task(db_session):
    task = Task(
        description="Test task",
        status="pending",
        assigned_agent="main"
    )
    db_session.add(task)
    db_session.commit()

    assert task.id is not None
    assert task.description == "Test task"
    assert task.status == "pending"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models.py::test_create_task -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.models'"

**Step 3: Create database.py**

Create `backend/src/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./open_cowork.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 4: Create models.py**

Create `backend/src/models.py`:
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    assigned_agent = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    parent = relationship("Task", remote_side=[id], backref="subtasks")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)  # JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(500), nullable=False, unique=True)
    access_level = Column(String(50), nullable=False)  # read, write, execute
    granted_at = Column(DateTime, default=datetime.utcnow)


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    cron_expression = Column(String(100), nullable=False)
    task_description = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)


class ComputerUsePermission(Base):
    __tablename__ = "computer_use_permissions"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(50), nullable=False)  # screenshot, mouse, keyboard, app_launch
    granted = Column(Boolean, default=False)
    scope = Column(String(200), nullable=True)  # global or specific app
    granted_at = Column(DateTime, default=datetime.utcnow)
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models.py::test_create_task -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/database.py backend/src/models.py backend/tests/test_models.py
git commit -m "feat: add database models and setup

- Add SQLAlchemy database configuration
- Add Task, Message, Permission, ScheduledJob, ComputerUsePermission models
- Add test for Task model creation"
```

---

## Phase 2: LLM Provider Abstraction

### Task 3: Create LLM Provider Base Class

**Files:**
- Create: `backend/src/llm/__init__.py`
- Create: `backend/src/llm/base.py`
- Create: `backend/tests/test_llm_base.py`

**Step 1: Write failing test for LLM provider interface**

Create `backend/tests/test_llm_base.py`:
```python
import pytest
from src.llm.base import LLMProvider, LLMResponse


def test_llm_provider_interface():
    """Test that LLMProvider defines required interface"""
    assert hasattr(LLMProvider, 'chat')
    assert hasattr(LLMProvider, 'stream')
    assert hasattr(LLMProvider, 'get_capabilities')


def test_llm_response_structure():
    """Test LLMResponse data structure"""
    response = LLMResponse(
        content="Hello",
        tool_calls=None,
        finish_reason="stop"
    )
    assert response.content == "Hello"
    assert response.tool_calls is None
    assert response.finish_reason == "stop"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_llm_base.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.llm'"

**Step 3: Create LLM base classes**

Create `backend/src/llm/__init__.py`:
```python
from .base import LLMProvider, LLMResponse

__all__ = ["LLMProvider", "LLMResponse"]
```

Create `backend/src/llm/base.py`:
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from pydantic import BaseModel


class LLMResponse(BaseModel):
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: str = "stop"


class LLMProvider(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat request and get response"""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response"""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities"""
        pass
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_llm_base.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/llm/ backend/tests/test_llm_base.py
git commit -m "feat: add LLM provider base classes

- Add LLMProvider abstract base class
- Add LLMResponse data model
- Add tests for provider interface"
```

---

### Task 4: Implement Claude Provider

**Files:**
- Create: `backend/src/llm/claude_provider.py`
- Create: `backend/tests/test_claude_provider.py`

**Step 1: Write failing test for Claude provider**

Create `backend/tests/test_claude_provider.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.llm.claude_provider import ClaudeProvider


@pytest.mark.asyncio
async def test_claude_chat():
    """Test Claude provider chat method"""
    with patch('src.llm.claude_provider.Anthropic') as mock_anthropic:
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Mock the messages.create response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello from Claude")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = ClaudeProvider(api_key="test-key")
        response = await provider.chat([{"role": "user", "content": "Hi"}])

        assert response.content == "Hello from Claude"
        assert response.finish_reason == "end_turn"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_claude_provider.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.llm.claude_provider'"

**Step 3: Implement Claude provider**

Create `backend/src/llm/claude_provider.py`:
```python
from typing import List, Dict, Any, Optional, AsyncIterator
from anthropic import Anthropic, AsyncAnthropic
from src.llm.base import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat request to Claude API"""
        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096)
        }

        if tools:
            params["tools"] = tools

        response = await self.client.messages.create(**params)

        # Extract text content
        content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                content += block.text

        # Extract tool calls if any
        tool_calls = None
        if hasattr(response, 'tool_use'):
            tool_calls = [
                {
                    "name": tool.name,
                    "input": tool.input
                }
                for tool in response.tool_use
            ]

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from Claude API"""
        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True
        }

        if tools:
            params["tools"] = tools

        async with self.client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                yield text

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Claude provider capabilities"""
        return {
            "provider": "claude",
            "model": self.model,
            "supports_streaming": True,
            "supports_tools": True,
            "supports_vision": True,
            "max_tokens": 200000
        }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_claude_provider.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/llm/claude_provider.py backend/tests/test_claude_provider.py
git commit -m "feat: implement Claude LLM provider

- Add ClaudeProvider with chat and stream methods
- Support tool use and streaming
- Add tests with mocked Anthropic client"
```

---

### Task 5: Implement OpenAI-Compatible Provider

**Files:**
- Create: `backend/src/llm/openai_provider.py`
- Create: `backend/tests/test_openai_provider.py`

**Step 1: Write failing test**

Create `backend/tests/test_openai_provider.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.llm.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_chat():
    """Test OpenAI-compatible provider chat method"""
    with patch('src.llm.openai_provider.AsyncOpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from OpenAI"
        mock_response.choices[0].finish_reason = "stop"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAIProvider(base_url="http://localhost:11434/v1", api_key="ollama")
        response = await provider.chat([{"role": "user", "content": "Hi"}])

        assert response.content == "Hello from OpenAI"
        assert response.finish_reason == "stop"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_openai_provider.py -v`
Expected: FAIL

**Step 3: Implement OpenAI provider**

Create `backend/src/llm/openai_provider.py`:
```python
from typing import List, Dict, Any, Optional, AsyncIterator
from openai import AsyncOpenAI
from src.llm.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        api_key: str = "not-needed",
        model: str = "llama3"
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat request to OpenAI-compatible API"""
        params = {
            "model": self.model,
            "messages": messages
        }

        if tools:
            params["tools"] = tools

        response = await self.client.chat.completions.create(**params)

        message = response.choices[0].message
        tool_calls = None

        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_calls = [
                {
                    "name": tc.function.name,
                    "input": tc.function.arguments
                }
                for tc in message.tool_calls
            ]

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            finish_reason=response.choices[0].finish_reason
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from OpenAI-compatible API"""
        params = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }

        if tools:
            params["tools"] = tools

        stream = await self.client.chat.completions.create(**params)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI provider capabilities"""
        return {
            "provider": "openai-compatible",
            "model": self.model,
            "base_url": self.base_url,
            "supports_streaming": True,
            "supports_tools": True
        }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_openai_provider.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/llm/openai_provider.py backend/tests/test_openai_provider.py
git commit -m "feat: implement OpenAI-compatible LLM provider

- Add OpenAIProvider for Ollama, LM Studio, vLLM, etc.
- Support chat, streaming, and tool use
- Add tests with mocked OpenAI client"
```

---

## Phase 3: Tool Registry & File Operations

### Task 6: Create Tool Registry Base

**Files:**
- Create: `backend/src/tools/__init__.py`
- Create: `backend/src/tools/base.py`
- Create: `backend/src/tools/registry.py`
- Create: `backend/tests/test_tool_registry.py`

**Step 1: Write failing test**

Create `backend/tests/test_tool_registry.py`:
```python
import pytest
from src.tools.registry import ToolRegistry
from src.tools.base import Tool


def test_tool_registry_register():
    """Test registering a tool"""
    registry = ToolRegistry()

    class DummyTool(Tool):
        name = "dummy"
        description = "A dummy tool"

        async def execute(self, **kwargs):
            return "dummy result"

    tool = DummyTool()
    registry.register(tool)

    assert "dummy" in registry.list_tools()
    assert registry.get_tool("dummy") == tool
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_tool_registry.py -v`
Expected: FAIL

**Step 3: Create tool base classes**

Create `backend/src/tools/__init__.py`:
```python
from .base import Tool
from .registry import ToolRegistry

__all__ = ["Tool", "ToolRegistry"]
```

Create `backend/src/tools/base.py`:
```python
from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """Base class for all tools"""

    name: str
    description: str
    parameters: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
```

Create `backend/src/tools/registry.py`:
```python
from typing import Dict, List, Optional
from src.tools.base import Tool


class ToolRegistry:
    """Registry for managing tools"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool"""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools"""
        return list(self._tools.values())

    def to_llm_format(self) -> List[Dict]:
        """Convert all tools to LLM format"""
        return [tool.to_dict() for tool in self._tools.values()]
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_tool_registry.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/tools/ backend/tests/test_tool_registry.py
git commit -m "feat: add tool registry system

- Add Tool base class
- Add ToolRegistry for managing tools
- Add tests for tool registration"
```

---

## Phase 4: File Operations Tools

### Task 7: Implement File Read Tool

**Files:**
- Create: `backend/src/tools/file_read.py`
- Create: `backend/tests/test_file_read.py`

**Step 1: Write failing test**

Create `backend/tests/test_file_read.py`:
```python
import pytest
import tempfile
import os
from src.tools.file_read import FileReadTool


@pytest.mark.asyncio
async def test_file_read_tool():
    """Test file read tool"""
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello World")
        temp_path = f.name

    try:
        tool = FileReadTool()
        result = await tool.execute(path=temp_path)

        assert result == "Hello World"
    finally:
        os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/test_file_read.py -v`
Expected: FAIL

**Step 3: Implement FileReadTool**

Create `backend/src/tools/file_read.py`:
```python
from src.tools.base import Tool
from typing import Any


class FileReadTool(Tool):
    name = "file_read"
    description = "Read contents of a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read"
            }
        },
        "required": ["path"]
    }

    async def execute(self, path: str, **kwargs) -> Any:
        """Read file contents"""
        with open(path, 'r') as f:
            return f.read()
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/test_file_read.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/tools/file_read.py backend/tests/test_file_read.py
git commit -m "feat: add file read tool

- Add FileReadTool for reading file contents
- Add tests for file read operations"
```

---

### Task 8: Implement File Write Tool

**Files:**
- Create: `backend/src/tools/file_write.py`
- Create: `backend/tests/test_file_write.py`

**Step 1: Write failing test**

Create `backend/tests/test_file_write.py`:
```python
import pytest
import tempfile
import os
from src.tools.file_write import FileWriteTool


@pytest.mark.asyncio
async def test_file_write_tool():
    """Test file write tool"""
    temp_path = tempfile.mktemp()

    try:
        tool = FileWriteTool()
        await tool.execute(path=temp_path, content="Test content")

        with open(temp_path, 'r') as f:
            assert f.read() == "Test content"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/test_file_write.py -v`
Expected: FAIL

**Step 3: Implement FileWriteTool**

Create `backend/src/tools/file_write.py`:
```python
from src.tools.base import Tool
from typing import Any


class FileWriteTool(Tool):
    name = "file_write"
    description = "Write content to a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["path", "content"]
    }

    async def execute(self, path: str, content: str, **kwargs) -> Any:
        """Write content to file"""
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/test_file_write.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/tools/file_write.py backend/tests/test_file_write.py
git commit -m "feat: add file write tool

- Add FileWriteTool for writing file contents
- Add tests for file write operations"
```

---

### Task 9: Implement Permission System

**Files:**
- Create: `backend/src/permissions.py`
- Create: `backend/tests/test_permissions.py`

**Step 1: Write failing test**

Create `backend/tests/test_permissions.py`:
```python
import pytest
from src.permissions import PermissionManager


def test_permission_check():
    """Test permission checking"""
    pm = PermissionManager()

    # No permission granted
    assert not pm.check_permission("/test/file.txt", "read")

    # Grant permission
    pm.grant_permission("/test/file.txt", "read")
    assert pm.check_permission("/test/file.txt", "read")

    # Check write permission (not granted)
    assert not pm.check_permission("/test/file.txt", "write")
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/test_permissions.py -v`
Expected: FAIL

**Step 3: Implement PermissionManager**

Create `backend/src/permissions.py`:
```python
from typing import Dict, Set


class PermissionManager:
    """Manage file and operation permissions"""

    def __init__(self):
        self._permissions: Dict[str, Set[str]] = {}

    def grant_permission(self, path: str, access_level: str):
        """Grant permission for a path"""
        if path not in self._permissions:
            self._permissions[path] = set()
        self._permissions[path].add(access_level)

    def revoke_permission(self, path: str, access_level: str):
        """Revoke permission for a path"""
        if path in self._permissions:
            self._permissions[path].discard(access_level)

    def check_permission(self, path: str, access_level: str) -> bool:
        """Check if permission is granted"""
        return path in self._permissions and access_level in self._permissions[path]

    def list_permissions(self) -> Dict[str, Set[str]]:
        """List all permissions"""
        return self._permissions.copy()
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/test_permissions.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/permissions.py backend/tests/test_permissions.py
git commit -m "feat: add permission management system

- Add PermissionManager for file access control
- Support grant, revoke, and check operations
- Add tests for permission system"
```

---

## Phase 5: Computer Use Tools

### Task 10: Implement Screenshot Tool

**Files:**
- Create: `backend/src/tools/screenshot.py`
- Create: `backend/tests/test_screenshot.py`

**Step 1: Write failing test**

Create `backend/tests/test_screenshot.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from src.tools.screenshot import ScreenshotTool


@pytest.mark.asyncio
async def test_screenshot_tool():
    """Test screenshot tool"""
    with patch('src.tools.screenshot.mss') as mock_mss:
        mock_sct = MagicMock()
        mock_mss.mss.return_value.__enter__.return_value = mock_sct
        mock_sct.shot.return_value = "/tmp/screenshot.png"

        tool = ScreenshotTool()
        result = await tool.execute()

        assert "screenshot.png" in result
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/test_screenshot.py -v`
Expected: FAIL

**Step 3: Implement ScreenshotTool**

Create `backend/src/tools/screenshot.py`:
```python
from src.tools.base import Tool
from typing import Any
import mss
import tempfile
import os


class ScreenshotTool(Tool):
    name = "screenshot"
    description = "Take a screenshot of the screen"
    parameters = {
        "type": "object",
        "properties": {}
    }

    async def execute(self, **kwargs) -> Any:
        """Take a screenshot"""
        with mss.mss() as sct:
            # Take screenshot of primary monitor
            output_path = os.path.join(tempfile.gettempdir(), "screenshot.png")
            sct.shot(output=output_path)
            return f"Screenshot saved to {output_path}"
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/test_screenshot.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/tools/screenshot.py backend/tests/test_screenshot.py
git commit -m "feat: add screenshot tool

- Add ScreenshotTool for capturing screen
- Add tests with mocked mss library"
```

---

### Task 11: Implement Mouse/Keyboard Control Tools

**Files:**
- Create: `backend/src/tools/mouse_keyboard.py`
- Create: `backend/tests/test_mouse_keyboard.py`

**Step 1: Write failing test**

Create `backend/tests/test_mouse_keyboard.py`:
```python
import pytest
from unittest.mock import patch
from src.tools.mouse_keyboard import MouseMoveTool, KeyboardTypeTool


@pytest.mark.asyncio
async def test_mouse_move_tool():
    """Test mouse move tool"""
    with patch('src.tools.mouse_keyboard.pyautogui') as mock_gui:
        tool = MouseMoveTool()
        await tool.execute(x=100, y=200)

        mock_gui.moveTo.assert_called_once_with(100, 200)


@pytest.mark.asyncio
async def test_keyboard_type_tool():
    """Test keyboard type tool"""
    with patch('src.tools.mouse_keyboard.pyautogui') as mock_gui:
        tool = KeyboardTypeTool()
        await tool.execute(text="Hello")

        mock_gui.write.assert_called_once_with("Hello")
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/test_mouse_keyboard.py -v`
Expected: FAIL

**Step 3: Implement Mouse/Keyboard tools**

Create `backend/src/tools/mouse_keyboard.py`:
```python
from src.tools.base import Tool
from typing import Any
import pyautogui


class MouseMoveTool(Tool):
    name = "mouse_move"
    description = "Move mouse to coordinates"
    parameters = {
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"}
        },
        "required": ["x", "y"]
    }

    async def execute(self, x: int, y: int, **kwargs) -> Any:
        """Move mouse to position"""
        pyautogui.moveTo(x, y)
        return f"Moved mouse to ({x}, {y})"


class MouseClickTool(Tool):
    name = "mouse_click"
    description = "Click mouse at current position"
    parameters = {
        "type": "object",
        "properties": {
            "button": {
                "type": "string",
                "enum": ["left", "right", "middle"],
                "description": "Mouse button to click"
            }
        }
    }

    async def execute(self, button: str = "left", **kwargs) -> Any:
        """Click mouse button"""
        pyautogui.click(button=button)
        return f"Clicked {button} mouse button"


class KeyboardTypeTool(Tool):
    name = "keyboard_type"
    description = "Type text using keyboard"
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to type"}
        },
        "required": ["text"]
    }

    async def execute(self, text: str, **kwargs) -> Any:
        """Type text"""
        pyautogui.write(text)
        return f"Typed: {text}"
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/test_mouse_keyboard.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/tools/mouse_keyboard.py backend/tests/test_mouse_keyboard.py
git commit -m "feat: add mouse and keyboard control tools

- Add MouseMoveTool, MouseClickTool, KeyboardTypeTool
- Add tests with mocked pyautogui"
```

---

## Phase 6: Agent Orchestration

### Task 12: Implement Agent Manager

**Files:**
- Create: `backend/src/agent_manager.py`
- Create: `backend/tests/test_agent_manager.py`

**Step 1: Write failing test**

Create `backend/tests/test_agent_manager.py`:
```python
import pytest
from src.agent_manager import AgentManager
from src.llm.base import LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    async def chat(self, messages, tools=None, **kwargs):
        return LLMResponse(content="Mock response", finish_reason="stop")

    async def stream(self, messages, tools=None, **kwargs):
        yield "Mock"
        yield " response"

    def get_capabilities(self):
        return {"provider": "mock"}


@pytest.mark.asyncio
async def test_agent_manager_execute():
    """Test agent manager execution"""
    provider = MockProvider()
    manager = AgentManager(provider)

    response = await manager.execute_task("Test task")

    assert "Mock response" in response
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/test_agent_manager.py -v`
Expected: FAIL

**Step 3: Implement AgentManager**

Create `backend/src/agent_manager.py`:
```python
from typing import List, Dict, Any, Optional
from src.llm.base import LLMProvider
from src.tools.registry import ToolRegistry


class AgentManager:
    """Manage agent execution and tool coordination"""

    def __init__(self, provider: LLMProvider, tool_registry: Optional[ToolRegistry] = None):
        self.provider = provider
        self.tool_registry = tool_registry or ToolRegistry()
        self.conversation_history: List[Dict[str, str]] = []

    async def execute_task(self, task: str) -> str:
        """Execute a task using the LLM and tools"""
        # Add user message
        self.conversation_history.append({
            "role": "user",
            "content": task
        })

        # Get tools in LLM format
        tools = self.tool_registry.to_llm_format() if self.tool_registry.list_tools() else None

        # Call LLM
        response = await self.provider.chat(
            messages=self.conversation_history,
            tools=tools
        )

        # Add assistant response
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        # Handle tool calls if any
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool = self.tool_registry.get_tool(tool_call["name"])
                if tool:
                    result = await tool.execute(**tool_call["input"])
                    # Add tool result to conversation
                    self.conversation_history.append({
                        "role": "user",
                        "content": f"Tool {tool_call['name']} result: {result}"
                    })

        return response.content

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/test_agent_manager.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/agent_manager.py backend/tests/test_agent_manager.py
git commit -m "feat: add agent manager for task execution

- Add AgentManager for coordinating LLM and tools
- Support conversation history and tool execution
- Add tests with mock provider"
```

---

## Phase 7: FastAPI Backend

### Task 13: Create FastAPI Application

**Files:**
- Create: `backend/src/main.py`
- Create: `backend/src/api/__init__.py`
- Create: `backend/src/api/routes.py`
- Create: `backend/tests/test_api.py`

**Step 1: Write failing test**

Create `backend/tests/test_api.py`:
```python
import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest tests/test_api.py -v`
Expected: FAIL

**Step 3: Create FastAPI application**

Create `backend/src/api/__init__.py`:
```python
# Empty init file
```

Create `backend/src/api/routes.py`:
```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@router.post("/chat")
async def chat(message: str):
    """Chat endpoint"""
    # TODO: Implement chat logic
    return {"response": "Not implemented yet"}
```

Create `backend/src/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.database import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Open-Cowork API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Open-Cowork API"}
```

**Step 4: Install test dependencies**

Run: `cd backend && source venv/bin/activate && pip install httpx`

**Step 5: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && pytest tests/test_api.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/main.py backend/src/api/ backend/tests/test_api.py
git commit -m "feat: add FastAPI application

- Add FastAPI app with CORS middleware
- Add health check endpoint
- Add API routes structure
- Add tests for API endpoints"
```

---

## Phase 8: Frontend Foundation

### Task 14: Setup Electron Main Process

**Files:**
- Create: `frontend/main.js`
- Create: `frontend/preload.js`
- Create: `frontend/index.html`

**Step 1: Create Electron main process**

Create `frontend/main.js`:
```javascript
const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Load index.html
  win.loadFile('index.html');

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    win.webContents.openDevTools();
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
```

**Step 2: Create preload script**

Create `frontend/preload.js`:
```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  sendMessage: (message) => ipcRenderer.invoke('send-message', message),
  onResponse: (callback) => ipcRenderer.on('response', callback)
});
```

**Step 3: Create basic HTML**

Create `frontend/index.html`:
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Open-Cowork</title>
  <style>
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #1e1e1e;
      color: #ffffff;
    }
    #root {
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
  </style>
</head>
<body>
  <div id="root">
    <h1>Open-Cowork</h1>
    <p>Loading...</p>
  </div>
</body>
</html>
```

**Step 4: Test Electron app**

Run: `cd frontend && npm start`
Expected: Electron window opens

**Step 5: Commit**

```bash
git add frontend/main.js frontend/preload.js frontend/index.html
git commit -m "feat: setup Electron main process

- Add Electron main process with window creation
- Add preload script for IPC communication
- Add basic HTML structure"
```

---

### Task 15: Setup React with Vite

**Files:**
- Create: `frontend/vite.config.js`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/index.css`

**Step 1: Create Vite config**

Create `frontend/vite.config.js`:
```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
});
```

**Step 2: Create React app**

Create `frontend/src/main.jsx`:
```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

Create `frontend/src/App.jsx`:
```jsx
import React, { useState } from 'react';

function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  const handleSend = async () => {
    // TODO: Connect to backend API
    setResponse('Backend not connected yet');
  };

  return (
    <div className="app">
      <header>
        <h1>Open-Cowork</h1>
      </header>
      <main>
        <div className="chat-container">
          <div className="messages">
            {response && <div className="message">{response}</div>}
          </div>
          <div className="input-area">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type a message..."
            />
            <button onClick={handleSend}>Send</button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
```

Create `frontend/src/index.css`:
```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #1e1e1e;
  color: #ffffff;
}

.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

header {
  padding: 1rem;
  background: #2d2d2d;
  border-bottom: 1px solid #3d3d3d;
}

main {
  flex: 1;
  overflow: hidden;
}

.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.message {
  background: #2d2d2d;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.input-area {
  padding: 1rem;
  background: #2d2d2d;
  border-top: 1px solid #3d3d3d;
  display: flex;
  gap: 0.5rem;
}

input {
  flex: 1;
  padding: 0.75rem;
  background: #1e1e1e;
  border: 1px solid #3d3d3d;
  border-radius: 4px;
  color: #ffffff;
  font-size: 1rem;
}

button {
  padding: 0.75rem 1.5rem;
  background: #007acc;
  border: none;
  border-radius: 4px;
  color: #ffffff;
  cursor: pointer;
  font-size: 1rem;
}

button:hover {
  background: #005a9e;
}
```

**Step 3: Update index.html to load React**

Update `frontend/index.html`:
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Open-Cowork</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
```

**Step 4: Test React app**

Run: `cd frontend && npm run dev`
Expected: Vite dev server starts

**Step 5: Commit**

```bash
git add frontend/vite.config.js frontend/src/ frontend/index.html
git commit -m "feat: setup React with Vite

- Add Vite configuration
- Add React app with basic chat UI
- Add styling for dark theme"
```

---

## Summary

This implementation plan now covers all phases:

**Phase 1-3: Foundation** (Tasks 1-6) ✓ COMPLETED
- Project structure
- Database models
- LLM provider abstraction (Claude + OpenAI-compatible)
- Tool registry system

**Phase 4: File Operations** (Tasks 7-9)
- File read/write tools
- Permission management system

**Phase 5: Computer Use** (Tasks 10-11)
- Screenshot tool
- Mouse/keyboard control tools

**Phase 6: Agent Orchestration** (Task 12)
- Agent manager for task execution

**Phase 7: Backend API** (Task 13)
- FastAPI application with endpoints

**Phase 8: Frontend** (Tasks 14-15)
- Electron main process
- React UI with Vite

**Next Steps:**
- Continue implementing Tasks 7-15
- Add integration tests
- Add documentation
- Package for distribution
