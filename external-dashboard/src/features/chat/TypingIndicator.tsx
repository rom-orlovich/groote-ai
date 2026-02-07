import { Bot, Loader2 } from "lucide-react";

interface TypingIndicatorProps {
  taskId: string;
  onTaskClick: (taskId: string) => void;
}

export function TypingIndicator({ taskId, onTaskClick }: TypingIndicatorProps) {
  return (
    <div className="flex gap-2 md:gap-4 mb-8 items-start animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="w-6 h-6 md:w-8 md:h-8 flex items-center justify-center flex-shrink-0 border border-primary/20 bg-primary/5 text-primary rounded-none shadow-sm">
        <Bot size={12} className="md:w-3.5 md:h-3.5" />
      </div>
      <div className="p-3 md:p-4 text-[10px] md:text-[11px] leading-relaxed border border-panel-border bg-panel-bg rounded-2xl rounded-tl-none shadow-sm">
        <div className="flex items-center gap-2 font-mono text-app-muted">
          <Loader2 size={12} className="animate-spin text-primary" />
          <span>PROCESSING</span>
          <button
            type="button"
            onClick={() => onTaskClick(taskId)}
            className="text-primary hover:underline font-bold cursor-pointer bg-primary/10 px-1 rounded-sm transition-colors hover:bg-primary/20"
          >
            {taskId}
          </button>
        </div>
      </div>
    </div>
  );
}
