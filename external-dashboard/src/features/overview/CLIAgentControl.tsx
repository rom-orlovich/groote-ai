import { AlertCircle, ChevronRight, Loader, Play, StopCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { useCLIAgentStatus, useStartCLIAgent, useStopCLIAgent } from "./hooks/useCLIAgentControl";

export function CLIAgentControl() {
  const { data: status, isLoading, error } = useCLIAgentStatus();
  const startMutation = useStartCLIAgent();
  const stopMutation = useStopCLIAgent();

  if (isLoading) {
    return (
      <div className="panel" data-label="CLI_AGENT_STATUS">
        <div className="flex items-center justify-center h-32">
          <Loader size={16} className="animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="panel" data-label="CLI_AGENT_STATUS">
        <div className="flex items-start gap-3 p-4 border border-red-200/30 bg-red-50/30 rounded">
          <AlertCircle size={16} className="text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-xs font-heading font-bold text-red-600">UNABLE_TO_FETCH_STATUS</p>
            <p className="text-[10px] text-red-500/70 mt-1">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const isLoading_ = startMutation.isPending || stopMutation.isPending;

  return (
    <div className="panel" data-label="CLI_AGENT_STATUS">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`w-3 h-3 rounded-full ${status.status === "running" ? "bg-green-500 animate-pulse" : "bg-red-500"}`}
            />
            <div>
              <div className="text-[10px] text-gray-400 font-heading">AGENT_STATUS</div>
              <div className="text-sm font-heading font-bold uppercase tracking-wide text-text-main">
                {status.status}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-gray-400 font-heading">ACTIVE_INSTANCES</div>
            <div className="text-2xl font-heading font-black text-primary">
              {status.active_instances}/{status.max_instances}
            </div>
          </div>
        </div>

        {status.health_check && (
          <div className="text-[10px] text-green-600 bg-green-50/50 border border-green-200/30 px-2 py-1 rounded">
            ✓ HEALTH_CHECK_OK
          </div>
        )}

        <div className="flex gap-2 pt-2 border-t border-panel-border">
          {status.status === "running" ? (
            <button
              type="button"
              onClick={() => stopMutation.mutate()}
              disabled={isLoading_}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-[10px] font-heading border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors disabled:opacity-50"
            >
              {isLoading_ ? (
                <Loader size={12} className="animate-spin" />
              ) : (
                <StopCircle size={12} />
              )}
              STOP_AGENT
            </button>
          ) : (
            <button
              type="button"
              onClick={() => startMutation.mutate()}
              disabled={isLoading_}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-[10px] font-heading border border-green-200 dark:border-green-800 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-950/30 transition-colors disabled:opacity-50"
            >
              {isLoading_ ? (
                <Loader size={12} className="animate-spin" />
              ) : (
                <Play size={12} />
              )}
              START_AGENT
            </button>
          )}

          <Link
            to="/settings/agents"
            className="flex items-center justify-center gap-1 px-3 py-2 text-[10px] font-heading border border-panel-border hover:bg-panel-bg transition-colors"
          >
            SCALE
            <ChevronRight size={10} />
          </Link>
        </div>

        <div className="text-[9px] text-app-muted pt-1">
          Last checked: {new Date(status.last_checked).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
