import React, { useState, useMemo } from 'react';
import { User, ChevronDown, ChevronRight, Activity, Sparkles } from 'lucide-react';

const MessageBubble = ({ text, isUser, steps = [] }) => {
  const [isStepsOpen, setIsStepsOpen] = useState(false);
  const hasSteps = steps && steps.length > 0;

  // Helper to determine step type for coloring
  const getStepType = (stepText) => {
    const text = stepText.toLowerCase();
    if (text.includes("thinking") || text.includes("planning")) return 'thinking';
    if (text.includes("done") || text.includes("completed") || text.includes("success")) return 'success';
    return 'action';
  };

  return (
    <div className={`flex gap-4 w-full ${isUser ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 fade-in duration-300 mb-6`}>
      
      {/* Avatar (Agent Side) */}
      {!isUser && (
        <div className="w-8 h-8 rounded-[10px] bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20 shadow-sm mt-0.5">
          <Sparkles className="w-4 h-4 text-primary" strokeWidth={2.5} />
        </div>
      )}

      {/* Message Content Area */}
      <div 
        className={`max-w-[85%] flex flex-col gap-3 ${
          isUser ? 'items-end' : 'items-start'
        }`}
      >
        {/* Premium Execution Steps Accordion */}
        {!isUser && hasSteps && (
          <div className="w-full mb-2 border border-black/[0.04] rounded-2xl overflow-hidden transition-all duration-300 relative">
            
            {/* Glass Background */}
            <div className="absolute inset-0 bg-white/40 backdrop-blur-md z-0"></div>
            
            {/* Outline/Highlight for Glass Effect */}
            <div className="absolute inset-0 border border-white/60 rounded-2xl z-0 pointer-events-none"></div>

            <div className="relative z-10 shadow-[0_2px_10px_-4px_rgba(0,0,0,0.05)]">
              {/* Header Toggle */}
              <button 
                onClick={() => setIsStepsOpen(!isStepsOpen)}
                className="flex items-center justify-between w-full px-4 py-3 text-text hover:bg-black/[0.02] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
              >
                <div className="flex items-center gap-2.5 font-medium text-[13px] tracking-wide text-text/90">
                  <div className="p-1 rounded-md bg-stone-100 text-stone-600 shadow-sm border border-black/5">
                    <Activity className="w-3.5 h-3.5" strokeWidth={2.5} />
                  </div>
                  <span>Execution Process ({steps.length})</span>
                </div>
                <div className="text-text-muted transition-transform duration-300">
                  {isStepsOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </div>
              </button>
              
              {/* Expandable Content Layer */}
              <div 
                className={`grid transition-[grid-template-rows,opacity] duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] ${
                  isStepsOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
                }`}
              >
                <div className="overflow-hidden">
                  <div className="px-4 pb-4 pt-1 border-t border-black/[0.04] space-y-3 max-h-[300px] overflow-y-auto font-mono text-xs">
                    {steps.map((step, idx) => {
                      const stepType = getStepType(step);
                      
                      // Node styling based on step context
                      const dotStyle = 
                        stepType === 'thinking' ? 'bg-stone-300 shadow-[0_0_6px_rgba(214,211,209,0.5)]' :
                        stepType === 'success' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]' :
                        'bg-primary shadow-[0_0_8px_rgba(217,119,87,0.4)]';

                      const dotAnimation = stepType === 'thinking' ? 'animate-pulse' : '';

                      return (
                        <div key={idx} className="group relative flex items-start gap-3.5 p-2 -mx-2 rounded-lg hover:bg-black/[0.03] transition-colors duration-200">
                          
                          {/* Timeline connector (if not last item) */}
                          {idx !== steps.length - 1 && (
                            <div className="absolute left-[13px] top-6 bottom-[-16px] w-[1px] bg-black/5 group-hover:bg-black/10 transition-colors"></div>
                          )}

                          {/* Animated Dot Indicator */}
                          <div className="mt-1.5 shrink-0 z-10 bg-white/50 backdrop-blur-sm rounded-full p-[3px]">
                            <div className={`w-1.5 h-1.5 rounded-full ${dotStyle} ${dotAnimation} transition-colors duration-300`} />
                          </div>
                          
                          {/* Step Content */}
                          <div className="flex flex-col gap-1 min-w-0">
                            <span className="text-[10px] font-bold tracking-widest text-text-muted/60 uppercase">
                              {stepType === 'thinking' ? 'Processing' : 
                               stepType === 'success' ? 'Complete' : 'Action'} {idx + 1}
                            </span>
                            <span className="text-[13px] text-text/80 leading-relaxed font-sans break-words select-text pt-0.5">
                              {step}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Text Bubble */}
        {text && (
          <div className={`px-5 py-3.5 text-[15px] leading-relaxed rounded-2xl ${
            isUser 
              ? 'bg-neutral-100/80 text-text rounded-br-[4px] shadow-sm border border-neutral-200/50' 
              : 'bg-transparent text-text'
          }`}>
             <p className="whitespace-pre-wrap font-sans break-words">{text}</p>
          </div>
        )}
      </div>

      {/* Avatar (User Side) */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-neutral-800 text-white flex items-center justify-center shrink-0 shadow-md border border-black/10 mt-0.5">
          <User className="w-4 h-4" strokeWidth={2.5} />
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
