# Open-Cowork

Open-source agentic desktop application with Claude Cowork-like capabilities.

## 🚀 Features

### Core Capabilities
- **Multi-step Task Execution** - Break down complex tasks into manageable steps
- **Sub-agent Coordination** - Orchestrate multiple AI agents working together
- **LLM Provider Abstraction** - Support for Claude API and OpenAI-compatible endpoints (Ollama, LM Studio, vLLM)

### File Operations
- **File Read/Write Tools** - Safe file system operations
- **Permission Management** - Granular access control for file operations

### Computer Use
- **Screenshot Capture** - Take screenshots programmatically
- **Mouse/Keyboard Control** - Automate UI interactions
- **App Launching** - Start and control applications

### Architecture
- **Backend**: Python FastAPI with async support
- **Frontend**: Electron + React + Vite
- **Database**: SQLite with SQLAlchemy ORM
- **Testing**: pytest with 100% test coverage for core modules

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

## 🛠️ Setup

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

## 🚀 Running the Application

### Start Backend Server

```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Start Frontend (Development)

```bash
cd frontend
npm run dev
```

### Start Electron App

```bash
cd frontend
npm start
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

### Run Specific Test

```bash
PYTHONPATH=. pytest tests/test_agent_manager.py -v
```

## 📁 Project Structure

```
open-cowork/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI routes
│   │   ├── llm/              # LLM provider implementations
│   │   ├── tools/            # Tool implementations
│   │   ├── agent_manager.py  # Agent orchestration
│   │   ├── database.py       # Database configuration
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── permissions.py    # Permission management
│   │   └── main.py           # FastAPI application
│   ├── tests/                # Test suite
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main React component
│   │   ├── main.jsx          # React entry point
│   │   └── index.css         # Styles
│   ├── main.js               # Electron main process
│   ├── preload.js            # Electron preload script
│   ├── index.html            # HTML template
│   ├── vite.config.js        # Vite configuration
│   └── package.json          # Node dependencies
└── docs/
    ├── plans/                # Implementation plans
    └── design/               # Design documents
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# LLM Configuration
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_BASE_URL=http://localhost:11434/v1  # For Ollama
OPENAI_API_KEY=not-needed  # For local models

# Database
DATABASE_URL=sqlite:///./open_cowork.db

# Server
HOST=0.0.0.0
PORT=8000
```

## 🏗️ Architecture

### Backend Components

1. **LLM Providers** (`src/llm/`)
   - `ClaudeProvider`: Anthropic Claude API integration
   - `OpenAIProvider`: OpenAI-compatible API support (Ollama, LM Studio, etc.)

2. **Tools** (`src/tools/`)
   - `FileReadTool`: Read file contents
   - `FileWriteTool`: Write to files
   - `ScreenshotTool`: Capture screenshots
   - `MouseMoveTool`, `MouseClickTool`: Mouse control
   - `KeyboardTypeTool`: Keyboard automation

3. **Agent Manager** (`src/agent_manager.py`)
   - Coordinates LLM and tool execution
   - Manages conversation history
   - Handles tool call routing

4. **Permission System** (`src/permissions.py`)
   - File access control
   - Operation authorization

### Frontend Components

- **Electron**: Desktop application wrapper
- **React**: UI framework
- **Vite**: Build tool and dev server

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions or modifications
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

## 📝 Development Status

### Completed ✅
- [x] Project structure and configuration
- [x] Database models and ORM setup
- [x] LLM provider abstraction (Claude + OpenAI-compatible)
- [x] Tool registry system
- [x] File operation tools
- [x] Permission management
- [x] Computer use tools (screenshot, mouse, keyboard)
- [x] Agent manager for task orchestration
- [x] FastAPI backend with health check
- [x] Electron + React frontend foundation

### In Progress 🚧
- [ ] WebSocket support for real-time communication
- [ ] Document generation (DOCX, XLSX, PPTX)
- [ ] WASM sandbox integration
- [ ] Advanced agent coordination
- [ ] UI/UX improvements

### Planned 📋
- [ ] Plugin system
- [ ] Multi-language support
- [ ] Cloud deployment options
- [ ] Performance monitoring
- [ ] Advanced security features

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Inspired by Claude Code and similar agentic systems
- Built with [Anthropic Claude API](https://www.anthropic.com/)
- Supports [Ollama](https://ollama.ai/) and other local LLM providers

## 📞 Support

- GitHub Issues: [Report bugs or request features](https://github.com/zmzhace/open-cowork/issues)
- Documentation: See `docs/` directory for detailed guides

---

**Note**: This is an early-stage project under active development. APIs and features may change.

