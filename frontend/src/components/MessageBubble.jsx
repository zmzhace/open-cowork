import React from 'react';
import { Sparkles, User } from 'lucide-react';

const MessageBubble = ({ text, isUser }) => {
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
        className={`max-w-[75%] px-4 py-3 text-[15px] leading-relaxed rounded-2xl ${
          isUser 
            ? 'bg-neutral-100 text-text rounded-br-sm' 
            : 'bg-transparent text-text'
        }`}
      >
        <p className="whitespace-pre-wrap font-sans break-words">{text}</p>
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
