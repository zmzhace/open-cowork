# 🚀 Open-Cowork: Your Intelligent Desktop Agent

Open-Cowork is an advanced, open-source agentic desktop application powered by Claude 3.5 Sonnet. It is designed to be your primary "Computer Use" companion, capable of automating complex GUI tasks, managing local files, and orchestrating system operations with human-like intelligence and extreme efficiency.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node-18%2B-green)](https://nodejs.org/)
[![Electron](https://img.shields.io/badge/Framework-Electron-brightgreen)](https://www.electronjs.org/)

---

## ✨ Key Features

### 🧠 High-Performance Computer Agent
- **Parallel Tool Execution**: Leverages Claude's multi-tool usage capabilities to perform independent tasks (checking processes, listing windows, reading files) simultaneously, reducing task completion time by **30-50%**.
- **Visual Intelligence**: Direct integration with system screenshots for real-time UI analysis and precise coordinate-based interaction.
- **Prompt Caching Optimized**: Utilizes Anthropic's Prompt Caching to significantly reduce API latency and token costs for long-running sessions.
- **Smart ReAct Loop**: Advanced reasoning-action-observation cycles with loop detection and pattern recognition (A-B-A-B detection).

### 🛠️ Comprehensive Toolset
- **GUI Automation**: Precise mouse clicks, keyboard input, and window management (focus, list, minimize/maximize).
- **System Control**: Process management (list/kill), command execution (powershell/sh), and clipboard operations.
- **File System**: Secure, permission-aware file reading and writing.
- **App Discovery**: Intelligent application path finding and launching.

### 🎨 Premium User Experience
- **Anthropic-Inspired Light Theme**: A clean, professional, and aesthetic UI designed for focus and clarity.
- **Real-Time Feedback**: Visual step-by-step logs of the Agent's thinking process and tool executions.
- **Modern Stack**: Built with **React 18**, **Vite**, **Electron**, and **Tailwind CSS 4.0**.

---

## 🏗️ Technical Architecture

### Backend: FastAPI
- **Modular Provider System**: Native support for Anthropic Claude (Sonnet/Haiku) and OpenAI-compatible endpoints.
- **Asynchronous Tooling**: All system tools are implemented with async support to prevent blocking the event loop.
- **Virtual Environment Ready**: Includes a robust `venv` setup guide for dependency isolation.

### Frontend: Electron + React
- **Electron Bridge**: Secure IPC communication between the web environment and system APIs.
- **Vite Bundler**: Ultra-fast development experience with Hot Module Replacement (HMR).
- **Lucide Icons**: Crisp, vector-based icons for a consistent visual language.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API Key (Claude 3.5 Sonnet recommended)

### Quick Start (Development)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/zmzhace/open-cowork.git
   cd open-cowork
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   # Copy .env.example to .env and add your API key
   ```

3. **Frontend Setup:**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Launch the Core:**
   - **Terminal 1 (Backend):** `python -m uvicorn src.main:app --reload`
   - **Terminal 2 (Frontend):** `npm run dev`

---

## 📁 Project Structure

```bash
open-cowork/
├── backend/
│   ├── src/
│   │   ├── agent/            # Optimized Computer Agent (ReAct loop)
│   │   ├── api/              # FastAPI endpoints (/chat, /health)
│   │   ├── tools/            # Low-level system integration tools
│   │   └── main.py           # Entry point
│   └── venv/                 # Python virtual environment
├── frontend/
│   ├── src/
│   │   ├── components/       # Premium UI components (Sidebar, MessageBubble)
│   │   └── App.jsx           # Main chat orchid
│   └── package.json          # Node configuration
└── docs/                     # Comprehensive performance & architecture analysis
```

---

## 🤝 Contributing

We welcome contributions! Please check out our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on code style, commit conventions, and our development workflow.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the raw power of **Anthropic's Computer Use** capabilities.
- Built for the community that believes in open, local-first agentic computing.

---
**Open-Cowork**: Making desktop automation intelligent, parallel, and beautiful.

