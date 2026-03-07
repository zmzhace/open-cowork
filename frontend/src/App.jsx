import React, { useState, useRef, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import MessageBubble from './components/MessageBubble';
import ChatInput from './components/ChatInput';

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm Open-Cowork, your intelligent desktop assistant. I can automate your local applications like WeChat, browse files, and run commands. How can I help you today?",
      isUser: false,
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (text) => {
    if (!text.trim()) return;

    // Add user message
    const userMsg = { id: Date.now(), text, isUser: true };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // TODO: Connect to backend actual endpoint when ready
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: text }),
      });

      const data = await res.json();
      
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, text: data.response || 'Task completed.', isUser: false }
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, text: `⚠️ Error connecting to backend: ${error.message}`, isUser: false }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden text-text font-sans">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col min-w-0 bg-background relative">
        {/* Top Title Bar */}
        <header className="h-16 flex items-center px-6 border-b border-border bg-surface/50 backdrop-blur-md z-10 shrink-0 drag-region">
          <h2 className="text-lg font-medium text-text no-drag-region">New Thread</h2>
        </header>

        {/* Messages List */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 no-drag-region scroll-smooth">
          <div className="max-w-4xl mx-auto space-y-6 flex flex-col w-full pb-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} text={msg.text} isUser={msg.isUser} />
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
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
    </div>
  );
}

export default App;
