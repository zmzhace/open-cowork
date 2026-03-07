import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Bot, Maximize2, X, GripHorizontal } from 'lucide-react';

const FloatingStatus = ({ status, stepCount, onExpand, onCancel }) => {
  const [position, setPosition] = useState({ x: window.innerWidth - 340, y: window.innerHeight - 100 });
  const [isDragging, setIsDragging] = useState(false);
  const dragOffset = useRef({ x: 0, y: 0 });
  const containerRef = useRef(null);

  // Parse step info from status text
  const getStepIcon = (text) => {
    if (!text) return '⏳';
    const lower = text.toLowerCase();
    if (lower.includes('thinking')) return '🧠';
    if (lower.includes('🔧') || lower.includes('tool')) return '🔧';
    if (lower.includes('done') || lower.includes('✅')) return '✅';
    if (lower.includes('💬')) return '💬';
    if (lower.includes('⚡')) return '⚡';
    return '⏳';
  };

  // Dragging logic
  const handleMouseDown = useCallback((e) => {
    if (e.target.closest('button')) return; // Don't drag when clicking buttons
    setIsDragging(true);
    dragOffset.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    };
    e.preventDefault();
  }, [position]);

  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;
    const newX = Math.max(0, Math.min(window.innerWidth - 320, e.clientX - dragOffset.current.x));
    const newY = Math.max(0, Math.min(window.innerHeight - 80, e.clientY - dragOffset.current.y));
    setPosition({ x: newX, y: newY });
  }, [isDragging]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Truncate long status text
  const displayStatus = status && status.length > 50 ? status.slice(0, 47) + '...' : status;

  return (
    <div
      ref={containerRef}
      onMouseDown={handleMouseDown}
      className="fixed z-[9999] select-none"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        cursor: isDragging ? 'grabbing' : 'grab',
      }}
    >
      <div className="w-[320px] rounded-2xl overflow-hidden shadow-[0_8px_32px_-4px_rgba(0,0,0,0.15)] border border-white/30 relative">
        {/* Glass background */}
        <div className="absolute inset-0 bg-white/70 backdrop-blur-xl z-0"></div>
        <div className="absolute inset-0 border border-white/50 rounded-2xl z-0 pointer-events-none"></div>

        <div className="relative z-10">
          {/* Header row */}
          <div className="flex items-center justify-between px-3 py-2.5">
            <div className="flex items-center gap-2 min-w-0 flex-1">
              {/* Agent icon with pulse animation */}
              <div className="w-7 h-7 rounded-[8px] bg-primary/15 flex items-center justify-center shrink-0 border border-primary/20">
                <Bot className="w-3.5 h-3.5 text-primary" strokeWidth={2.5} />
              </div>

              {/* Status text */}
              <div className="flex flex-col min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-bold tracking-wider text-primary uppercase">
                    Executing
                  </span>
                  {stepCount > 0 && (
                    <span className="text-[10px] text-text-muted">
                      · {stepCount} steps
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[11px]">{getStepIcon(status)}</span>
                  <span className="text-[12px] text-text/80 truncate font-medium">
                    {displayStatus || 'Initializing...'}
                  </span>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-1 shrink-0 ml-2">
              <button
                onClick={onExpand}
                className="p-1.5 rounded-lg hover:bg-black/5 text-text-muted hover:text-text transition-colors"
                title="展开完整界面"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Animated progress bar */}
          <div className="h-[2px] bg-black/5 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary/60 via-primary to-primary/60 animate-pulse"
              style={{
                width: '60%',
                animation: 'shimmer 2s ease-in-out infinite',
              }}
            />
          </div>
        </div>
      </div>

      {/* Drag hint - subtle grip at the bottom */}
      <div className="flex justify-center mt-1">
        <GripHorizontal className="w-4 h-4 text-black/10" />
      </div>

      {/* Shimmer keyframe */}
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); width: 40%; }
          50% { transform: translateX(100%); width: 60%; }
          100% { transform: translateX(-100%); width: 40%; }
        }
      `}</style>
    </div>
  );
};

export default FloatingStatus;
