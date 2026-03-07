import { Sparkles, Maximize2 } from 'lucide-react';

const FloatingStatus = ({ status, stepCount, onExpand }) => {
  // Parse step info from status text
  const getStepLabel = (text) => {
    if (!text) return 'Initializing...';
    if (text.toLowerCase().includes('thinking')) return 'Thinking...';
    if (text.includes('[tool]')) return text.replace('[tool] ', '');
    if (text.includes('[reply]')) return text.replace('[reply] ', '');
    if (text.includes('Done')) return 'Completed';
    return text;
  };

  const displayStatus = getStepLabel(status);
  const truncated = displayStatus.length > 45 ? displayStatus.slice(0, 42) + '...' : displayStatus;

  return (
    <div className="fixed inset-0 w-full h-full bg-gradient-to-br from-white/90 to-neutral-50/90 backdrop-blur-xl z-[9999] flex flex-col select-none drag-region">
      {/* Main content */}
      <div className="flex items-center justify-between px-4 py-2 flex-1 no-drag-region">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {/* Animated agent icon */}
          <div className="w-8 h-8 rounded-xl bg-primary/15 flex items-center justify-center shrink-0 border border-primary/20">
            <Sparkles className="w-4 h-4 text-primary animate-pulse" strokeWidth={2.5} />
          </div>

          {/* Status text */}
          <div className="flex flex-col min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold tracking-wider text-primary uppercase">
                Executing
              </span>
              {stepCount > 0 && (
                <span className="text-[11px] text-text-muted font-medium">
                  · {stepCount} steps
                </span>
              )}
            </div>
            <span className="text-[13px] text-text/80 truncate font-medium mt-0.5">
              {truncated}
            </span>
          </div>
        </div>

        {/* Expand button */}
        <button
          onClick={onExpand}
          className="p-2 rounded-lg hover:bg-black/5 text-text-muted hover:text-text transition-colors shrink-0"
          title="Expand"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-[2px] bg-neutral-200 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-primary/50 via-primary to-primary/50"
          style={{
            animation: 'shimmer 2s ease-in-out infinite',
          }}
        />
      </div>

      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); width: 40%; }
          50% { transform: translateX(200%); width: 50%; }
          100% { transform: translateX(-100%); width: 40%; }
        }
      `}</style>
    </div>
  );
};

export default FloatingStatus;

