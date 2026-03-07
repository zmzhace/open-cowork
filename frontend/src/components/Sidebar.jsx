import React from 'react';
import { MessageSquare, Settings, PlusCircle, Sparkles, Zap, Trash2 } from 'lucide-react';

const Sidebar = ({ threads = [], currentThreadId, onSelectThread, onNewThread, onOpenSettings }) => {
  return (
    <aside className="w-64 bg-surface border-r border-border h-full flex flex-col">
      {/* Header (Drag Region) */}
      <div className="h-16 flex items-center px-4 border-b border-border drag-region">
        <div className="flex items-center gap-2.5 text-text pl-1 no-drag-region">
          <div className="w-7 h-7 rounded-[0.4rem] bg-primary/10 flex items-center justify-center border border-primary/20 shadow-sm">
            <Sparkles className="w-4 h-4 text-primary" strokeWidth={2.5} />
          </div>
          <span className="font-semibold text-[17px] tracking-tight">Open-Cowork</span>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-4 no-drag-region">
        <button 
          onClick={onNewThread}
          className="w-full bg-primary hover:bg-primary-hover text-white flex items-center justify-center gap-2 py-2.5 rounded-lg transition-all duration-200 font-medium shadow-sm hover:shadow active:scale-[0.98]"
        >
          <PlusCircle className="w-4 h-4" />
          New Thread
        </button>
      </div>

      {/* Chat History List */}
      <div className="flex-1 overflow-y-auto px-3 space-y-1 no-drag-region">
        <div className="text-xs font-semibold text-text-muted mb-3 uppercase tracking-wider px-2 mt-4 flex items-center justify-between">
          <span>Recent</span>
        </div>
        
        {threads.map((thread) => {
          const isActive = thread.id === currentThreadId;
          return (
            <button 
              key={thread.id}
              onClick={() => onSelectThread(thread.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors border group ${
                isActive 
                  ? 'bg-neutral-100 text-text border-transparent font-medium' 
                  : 'text-text-muted hover:bg-neutral-50 hover:text-text border-transparent'
              }`}
            >
              <MessageSquare className={`w-4 h-4 shrink-0 ${isActive ? 'text-primary' : 'text-text-muted group-hover:text-text'}`} />
              <span className="text-sm truncate flex-1">{thread.title || 'New Thread'}</span>
            </button>
          );
        })}
      </div>

      {/* Footer / Settings */}
      <div className="p-4 border-t border-border no-drag-region">
        <button 
          onClick={onOpenSettings}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-text hover:bg-neutral-100 transition-colors"
        >
          <Settings className="w-4 h-4 text-text-muted" />
          <span className="text-sm font-medium">Settings</span>
        </button>
        <div className="mt-4 flex items-center gap-2 px-3">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse ring-2 ring-emerald-500/20"></div>
          <span className="text-xs text-text-muted font-medium flex items-center gap-1">
            Agent <Zap className="w-3 h-3 text-yellow-500" /> V1
          </span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
