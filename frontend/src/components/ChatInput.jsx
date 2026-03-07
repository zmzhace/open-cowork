import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';

const ChatInput = ({ onSend, disabled }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText('');
    
    // Reset height explicitly
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  return (
    <div className="relative w-full group">
      <div className="relative flex items-end gap-2 bg-surface p-2 rounded-2xl border border-border shadow-sm focus-within:border-primary/30 focus-within:ring-1 focus-within:ring-primary/20 transition-all">
        
        {/* Decorative AI Icon */}
        <div className="p-3 shrink-0 text-text-muted">
          <Sparkles className="w-5 h-5" />
        </div>

        {/* Dynamic Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Open-Cowork to perform a task..."
          className="flex-1 max-h-[120px] py-3 bg-transparent text-text placeholder-text-muted resize-none outline-none text-[15px] leading-relaxed"
          rows={1}
          disabled={disabled}
        />

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          className="shrink-0 p-3 mb-0.5 mr-0.5 rounded-xl bg-primary hover:bg-primary-hover disabled:bg-neutral-200 disabled:text-neutral-400 text-white transition-all transform active:scale-95 flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default ChatInput;
