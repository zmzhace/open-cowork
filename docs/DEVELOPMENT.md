# Development Guide

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/zmzhace/open-cowork.git
cd open-cowork
```

2. Set up backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

3. Set up frontend:
```bash
cd frontend
npm install
```

## Development Workflow

### Backend Development

#### Running Tests
```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

#### Running with Auto-Reload
```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Testing Individual Components

**Test LLM Providers:**
```bash
PYTHONPATH=. pytest tests/test_claude_provider.py -v
PYTHONPATH=. pytest tests/test_openai_provider.py -v
```

**Test Tools:**
```bash
PYTHONPATH=. pytest tests/test_file_read.py -v
PYTHONPATH=. pytest tests/test_screenshot.py -v
```

**Test Agent Manager:**
```bash
PYTHONPATH=. pytest tests/test_agent_manager.py -v
```

### Frontend Development

#### Running Dev Server
```bash
cd frontend
npm run dev
```

#### Running Electron
```bash
cd frontend
npm start
```

#### Building for Production
```bash
cd frontend
npm run build
```

## Project Structure

```
open-cowork/
├── backend/
│   ├── src/
│   │   ├── api/              # API routes
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── llm/              # LLM providers
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── claude_provider.py
│   │   │   └── openai_provider.py
│   │   ├── tools/            # Tool implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── registry.py
│   │   │   ├── file_read.py
│   │   │   ├── file_write.py
│   │   │   ├── screenshot.py
│   │   │   └── mouse_keyboard.py
│   │   ├── agent_manager.py  # Agent orchestration
│   │   ├── database.py       # Database config
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── permissions.py    # Permission system
│   │   └── main.py           # FastAPI app
│   ├── tests/                # Test suite
│   │   ├── test_*.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── main.js               # Electron main
│   ├── preload.js            # Electron preload
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    └── plans/
```

## Adding New Features

### Adding a New LLM Provider

1. Create provider file in `backend/src/llm/`:
```python
# backend/src/llm/gemini_provider.py
from src.llm.base import LLMProvider, LLMResponse

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def chat(self, messages, tools=None, **kwargs):
        # Implementation
        pass

    async def stream(self, messages, tools=None, **kwargs):
        # Implementation
        pass

    def get_capabilities(self):
        return {
            "provider": "gemini",
            "supports_streaming": True,
            "supports_tools": True
        }
```

2. Create tests:
```python
# backend/tests/test_gemini_provider.py
import pytest
from src.llm.gemini_provider import GeminiProvider

@pytest.mark.asyncio
async def test_gemini_chat():
    # Test implementation
    pass
```

3. Run tests:
```bash
PYTHONPATH=. pytest tests/test_gemini_provider.py -v
```

### Adding a New Tool

1. Create tool file in `backend/src/tools/`:
```python
# backend/src/tools/web_search.py
from src.tools.base import Tool

class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    }

    async def execute(self, query: str, **kwargs):
        # Implementation
        return results
```

2. Create tests:
```python
# backend/tests/test_web_search.py
import pytest
from src.tools.web_search import WebSearchTool

@pytest.mark.asyncio
async def test_web_search():
    tool = WebSearchTool()
    result = await tool.execute(query="test")
    assert result is not None
```

3. Register tool:
```python
from src.tools.registry import ToolRegistry
from src.tools.web_search import WebSearchTool

registry = ToolRegistry()
registry.register(WebSearchTool())
```

## Debugging

### Backend Debugging

Add breakpoints using `pdb`:
```python
import pdb; pdb.set_trace()
```

Or use VS Code debugger with this launch configuration:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--reload"
      ],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Frontend Debugging

Use Chrome DevTools in Electron:
- Press `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)
- Or set `NODE_ENV=development` to auto-open DevTools

## Common Issues

### Import Errors

If you get `ModuleNotFoundError`, ensure `PYTHONPATH` is set:
```bash
export PYTHONPATH=/path/to/open-cowork/backend
```

Or run tests with:
```bash
PYTHONPATH=. pytest tests/ -v
```

### Database Issues

Reset database:
```bash
cd backend
rm open_cowork.db
python -c "from src.database import Base, engine; Base.metadata.create_all(engine)"
```

### Port Already in Use

Change port in backend:
```bash
uvicorn src.main:app --reload --port 8001
```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Max line length: 100
- Use `black` for formatting:
```bash
pip install black
black backend/src/
```

### JavaScript/React
- Use ES6+
- Functional components
- Use Prettier for formatting:
```bash
npm install -g prettier
prettier --write frontend/src/
```

## Testing Best Practices

1. **Write tests first** (TDD)
2. **Test one thing per test**
3. **Use descriptive names**
4. **Mock external dependencies**
5. **Aim for >80% coverage**

Example test structure:
```python
def test_feature_name():
    """Test that feature does X when Y"""
    # Arrange
    setup_data()

    # Act
    result = function_under_test()

    # Assert
    assert result == expected
```

## Performance Tips

1. **Use async/await** for I/O operations
2. **Cache expensive operations**
3. **Use connection pooling** for database
4. **Stream large responses**
5. **Lazy load tools**

## Security Checklist

- [ ] Validate all user inputs
- [ ] Use parameterized queries
- [ ] Check file permissions
- [ ] Sanitize file paths
- [ ] Rate limit API endpoints
- [ ] Use HTTPS in production
- [ ] Keep dependencies updated

## Deployment

### Backend Deployment

1. Set production environment variables
2. Use production ASGI server (Gunicorn + Uvicorn)
3. Set up reverse proxy (Nginx)
4. Enable HTTPS
5. Configure logging

### Frontend Deployment

1. Build production bundle:
```bash
npm run build
```

2. Package Electron app:
```bash
npm run package
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Electron Documentation](https://www.electronjs.org/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Anthropic API Documentation](https://docs.anthropic.com/)
