import React, { useState, useRef, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import MessageBubble from './components/MessageBubble';
import ChatInput from './components/ChatInput';
import FloatingStatus from './components/FloatingStatus';

function App() {
  const [threads, setThreads] = useState(() => {
    const saved = localStorage.getItem('opencowork_threads');
    return saved ? JSON.parse(saved) : [{ id: 1, title: 'New Thread', messages: [{ id: 1, text: "Hello! I'm Open-Cowork, your intelligent desktop assistant. I can automate your local applications like WeChat, browse files, and run commands. How can I help you today?", isUser: false }] }];
  });
  
  const [currentThreadId, setCurrentThreadId] = useState(() => {
    const saved = localStorage.getItem('opencowork_current_thread');
    return saved ? JSON.parse(saved) : 1;
  });

  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState('');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isMiniMode, setIsMiniMode] = useState(false);
  const [currentStepCount, setCurrentStepCount] = useState(0);
  
  // Settings State
  const [apiUrl, setApiUrl] = useState(() => localStorage.getItem('opencowork_api_url') || '');
  const [modelName, setModelName] = useState(() => localStorage.getItem('opencowork_model') || '');
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('opencowork_api_key') || '');

  const messagesEndRef = useRef(null);

  const currentThread = threads.find(t => t.id === currentThreadId) || threads[0];
  const messages = currentThread.messages;

  useEffect(() => {
    localStorage.setItem('opencowork_threads', JSON.stringify(threads));
    localStorage.setItem('opencowork_current_thread', JSON.stringify(currentThreadId));
  }, [threads, currentThreadId]);

  useEffect(() => {
    localStorage.setItem('opencowork_api_url', apiUrl);
    localStorage.setItem('opencowork_model', modelName);
    localStorage.setItem('opencowork_api_key', apiKey);
  }, [apiUrl, modelName, apiKey]);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, agentStatus]);

  // Sync mini-mode state with Electron
  useEffect(() => {
    if (window.electronAPI?.setMiniMode) {
      window.electronAPI.setMiniMode(isMiniMode);
    }
  }, [isMiniMode]);

  const handleSend = async (text) => {
    if (!text.trim()) return;

    const userMsg = { id: Date.now(), text, isUser: true };
    const assistantMsgId = Date.now() + 1;
    const initialAssistantMsg = { id: assistantMsgId, text: '', isUser: false, steps: [] };
    
    // Update thread with user message and potentially set title
    setThreads(prev => prev.map(t => {
      if (t.id === currentThreadId) {
        // Only set title automatically if it's "New Thread"
        const newTitle = t.title === 'New Thread' ? text.slice(0, 30) + (text.length > 30 ? '...' : '') : t.title;
        return { ...t, title: newTitle, messages: [...t.messages, userMsg, initialAssistantMsg] };
      }
      return t;
    }));

    setIsLoading(true);
    setAgentStatus('Initializing agent...');
    setIsMiniMode(true);
    setCurrentStepCount(0);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout for initial connection

      const payload = {
        message: text,
        base_url: apiUrl.trim() !== '' ? apiUrl.trim() : null,
        model: modelName.trim() !== '' ? modelName.trim() : null,
        api_key: apiKey.trim() !== '' ? apiKey.trim() : null
      };

      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;
      let buffer = "";

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop(); // keep incomplete line
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.substring(6));
                if (data.type === 'step') {
                  setAgentStatus(data.content);
                  setCurrentStepCount(prev => prev + 1);
                  setThreads(prev => prev.map(t => {
                    if (t.id === currentThreadId) {
                      return { ...t, messages: t.messages.map(m => m.id === assistantMsgId ? { ...m, steps: [...(m.steps || []), data.content] } : m) };
                    }
                    return t;
                  }));
                } else if (data.type === 'result') {
                  setAgentStatus('');
                  setThreads(prev => prev.map(t => {
                    if (t.id === currentThreadId) {
                      return { ...t, messages: t.messages.map(m => m.id === assistantMsgId ? { ...m, text: data.content || 'Task completed.' } : m) };
                    }
                    return t;
                  }));
                } else if (data.type === 'error') {
                  setAgentStatus('');
                  setThreads(prev => prev.map(t => {
                    if (t.id === currentThreadId) {
                      return { ...t, messages: t.messages.map(m => m.id === assistantMsgId ? { ...m, text: `⚠️ Agent Error: ${data.content}` } : m) };
                    }
                    return t;
                  }));
                }
              } catch (e) {
                console.error("Error parsing SSE data line", line, e);
              }
            }
          }
        }
      }
    } catch (error) {
      const fetchErrorMsg = { id: Date.now() + 2, text: `⚠️ Error connecting to backend: ${error.message}`, isUser: false };
      setThreads(prev => prev.map(t => t.id === currentThreadId ? { ...t, messages: [...t.messages, fetchErrorMsg] } : t));
    } finally {
      setIsLoading(false);
      setAgentStatus('');
      setIsMiniMode(false);
      setCurrentStepCount(0);
    }
  };

  const handleNewThread = () => {
    const newId = Date.now();
    const newThread = {
      id: newId,
      title: 'New Thread',
      messages: [{ id: 1, text: "Hello! I'm Open-Cowork, your intelligent desktop assistant. I can automate your local applications like WeChat, browse files, and run commands. How can I help you today?", isUser: false }]
    };
    setThreads(prev => [newThread, ...prev]);
    setCurrentThreadId(newId);
  };

  const handleDeleteThread = (id) => {
    if (threads.length <= 1) {
      alert("At least one thread must remain.");
      return;
    }
    if (window.confirm("Are you sure you want to delete this thread?")) {
      const remainingThreads = threads.filter(t => t.id !== id);
      setThreads(remainingThreads);
      if (currentThreadId === id) {
        setCurrentThreadId(remainingThreads[0].id);
      }
    }
  };

  return (
    <>
    {/* Floating Mini Status (visible in mini mode) */}
    {isMiniMode && (
      <FloatingStatus
        status={agentStatus}
        stepCount={currentStepCount}
        onExpand={() => setIsMiniMode(false)}
      />
    )}

    <div className={`flex h-screen w-full bg-background overflow-hidden text-text font-sans transition-opacity duration-300 ${isMiniMode ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
      {/* Sidebar */}
      <Sidebar 
        threads={threads} 
        currentThreadId={currentThreadId} 
        onSelectThread={setCurrentThreadId} 
        onNewThread={handleNewThread}
        onDeleteThread={handleDeleteThread}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative h-full min-w-0">
        {/* Top Title Bar */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-border bg-surface/50 backdrop-blur-md z-10 shrink-0 drag-region">
          <h2 className="text-lg font-medium text-text no-drag-region">{currentThread.title}</h2>
          
          {/* macOS Traffic Lights (Moved to Right) */}
          <div className="flex gap-2 no-drag-region">
            <button 
              onClick={() => window.electronAPI.minimize()}
              className="w-3 h-3 rounded-full bg-[#ffbd2e] border border-[#dea123] hover:brightness-90 transition-all group relative"
            >
              <span className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 text-[8px] text-black/50">−</span>
            </button>
            <button 
              onClick={() => window.electronAPI.maximize()}
              className="w-3 h-3 rounded-full bg-[#27c93f] border border-[#1aab29] hover:brightness-90 transition-all group relative"
            >
              <span className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 text-[8px] text-black/50">+</span>
            </button>
            <button 
              onClick={() => window.electronAPI.close()}
              className="w-3 h-3 rounded-full bg-[#ff5f56] border border-[#e0443e] hover:brightness-90 transition-all group relative"
            >
              <span className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 text-[8px] text-black/50">×</span>
            </button>
          </div>
        </header>

        {/* Messages List */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 no-drag-region scroll-smooth">
          <div className="max-w-4xl mx-auto space-y-6 flex flex-col w-full pb-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} text={msg.text} isUser={msg.isUser} steps={msg.steps} />
            ))}
            
            {/* Agent Status */}
            {agentStatus && (
              <div className="flex gap-2 items-center text-sm text-text-muted bg-surface/50 border border-border px-3 py-2 rounded-lg w-fit animate-in fade-in duration-300 mb-2">
                <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin shrink-0"></div>
                <span>{agentStatus}</span>
              </div>
            )}
            
            {/* Loading Indicator */}
            {isLoading && !agentStatus && (
              <div className="flex gap-4 w-full justify-start animate-in fade-in duration-300">
                <div className="w-8 h-8 rounded-lg bg-surface flex items-center justify-center shrink-0 border border-border shadow-sm">
                  <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 sm:p-6 lg:px-8 shrink-0 bg-gradient-to-t from-background via-background to-transparent no-drag-region">
          <div className="max-w-4xl mx-auto mb-2">
            <ChatInput onSend={handleSend} disabled={isLoading} />
            <div className="text-center mt-3 text-xs text-text-muted">
              Open-Cowork can automate GUI applications, read files, and manage your local environment.
            </div>
          </div>
        </div>
      </main>

      {/* Settings Modal Stub */}
      {isSettingsOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-surface w-full max-w-md rounded-2xl shadow-xl border border-border overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <h3 className="text-lg font-semibold text-text">Settings</h3>
              <button onClick={() => setIsSettingsOpen(false)} className="text-text-muted hover:text-text transition-colors p-1 rounded-md hover:bg-neutral-100">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-sm font-medium text-text">API Base URL</label>
                <input 
                  type="text" 
                  placeholder="e.g. https://api.anthropic.com" 
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  className="w-full bg-neutral-100 border border-border rounded-lg px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow" 
                />
                <p className="text-xs text-text-muted">Leave empty to use backend .env default.</p>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-text">Default Model</label>
                <input 
                  type="text" 
                  placeholder="e.g. claude-sonnet-4-6" 
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full bg-neutral-100 border border-border rounded-lg px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow" 
                />
                <p className="text-xs text-text-muted">Currently active model used by the agent.</p>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-text">API Key</label>
                <input 
                  type="password" 
                  placeholder="sk-ant-..." 
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-neutral-100 border border-border rounded-lg px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow" 
                />
                <p className="text-xs text-text-muted">Optional local override for backend .env.</p>
              </div>
            </div>
            <div className="px-6 py-4 bg-neutral-50 border-t border-border flex justify-end">
              <button onClick={() => setIsSettingsOpen(false)} className="px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-hover transition-colors shadow-sm">Done</button>
            </div>
          </div>
        </div>
      )}
    </div>
    </>
  );
}

export default App;
