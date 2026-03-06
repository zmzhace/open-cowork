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
