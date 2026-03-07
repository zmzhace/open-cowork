import React, { useState } from 'react';
import { Sparkles, User, ChevronDown, ChevronRight, Activity } from 'lucide-react';

const MessageBubble = ({ text, isUser, steps = [] }) => {
  const [isStepsOpen, setIsStepsOpen] = useState(false);
  const hasSteps = steps && steps.length > 0;

  return (
    <div className={`flex gap-4 w-full ${isUser ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 fade-in duration-300`}>
      {/* Avatar (Agent Side) */}
      {!isUser && (
        <div className="w-8 h-8 rounded-[0.4rem] bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20 shadow-sm mt-0.5">
          <Sparkles className="w-4 h-4 text-primary" strokeWidth={2.5} />
        </div>
      )}

      {/* Message Content */}
      <div 
        className={`max-w-[85%] flex flex-col gap-2 ${
          isUser ? 'items-end' : 'items-start'
        }`}
      >
        {/* Main Text Bubble */}
        {text && (
          <div className={`px-4 py-3 text-[15px] leading-relaxed rounded-2xl ${
            isUser ? 'bg-neutral-100 text-text rounded-br-sm' : 'bg-transparent text-text'
          }`}>
             <p className="whitespace-pre-wrap font-sans break-words">{text}</p>
          </div>
        )}

        {/* Execution Steps Accordion */}
        {!isUser && hasSteps && (
          <div className="w-full mt-1 border border-border rounded-xl bg-surface/50 overflow-hidden text-sm shadow-sm transition-all duration-200">
            <button 
              onClick={() => setIsStepsOpen(!isStepsOpen)}
              className="flex items-center justify-between w-full px-4 py-2.5 text-text hover:bg-neutral-50 transition-colors"
            >
              <div className="flex items-center gap-2 font-medium">
                <Activity className="w-4 h-4 text-primary" />
                <span>Execution Steps ({steps.length})</span>
              </div>
              {isStepsOpen ? <ChevronDown className="w-4 h-4 text-text-muted" /> : <ChevronRight className="w-4 h-4 text-text-muted" />}
            </button>
            
            {isStepsOpen && (
              <div className="px-4 py-3 bg-neutral-50/50 border-t border-border space-y-2 max-h-60 overflow-y-auto font-mono text-xs shadow-inner">
                {steps.map((step, idx) => (
                  <div key={idx} className="flex gap-2 text-text-muted">
                    <span className="text-neutral-400 shrink-0 select-none">[{idx + 1}]</span>
                    <span className="break-all">{step}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Avatar (User Side) */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center shrink-0 border border-primary/20 shadow-sm mt-0.5">
          <User className="w-5 h-5" />
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
