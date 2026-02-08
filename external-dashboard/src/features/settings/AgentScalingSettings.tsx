import { AlertCircle, CheckCircle, Loader } from "lucide-react";
import { useEffect, useState } from "react";
import { useAgentScalingConfig, useSaveAgentScaling } from "./hooks/useAgentScaling";

interface ScalingConfig {
  agent_count: number;
  min_agents: number;
  max_agents: number;
  queue_size?: number;
  estimated_cost?: number;
}

export function AgentScalingSettings() {
  const [config, setConfig] = useState<ScalingConfig>({
    agent_count: 5,
    min_agents: 1,
    max_agents: 20,
  });
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const { isLoading, data } = useAgentScalingConfig();
  const saveMutation = useSaveAgentScaling();

  useEffect(() => {
    if (data) {
      setConfig(data);
    }
  }, [data]);

  useEffect(() => {
    if (saveMutation.isSuccess) {
      setMessage({ type: "success", text: "Agent scaling applied" });
      setTimeout(() => setMessage(null), 3000);
    }
  }, [saveMutation.isSuccess]);

  useEffect(() => {
    if (saveMutation.isError) {
      setMessage({ type: "error", text: "Failed to apply scaling" });
    }
  }, [saveMutation.isError]);

  const handleSave = () => {
    saveMutation.mutate(config.agent_count);
  };

  const costPerAgent = 0.05;
  const estimatedMonthlyCost = config.agent_count * costPerAgent * 730;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-app-muted font-heading">LOADING_SETTINGS...</div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6 animate-in fade-in duration-500">
      {message && (
        <div
          className={`flex items-center gap-3 p-4 border text-[10px] font-heading ${
            message.type === "success"
              ? "border-green-200 dark:border-green-800 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/30"
              : "border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30"
          }`}
        >
          {message.type === "success" ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="panel" data-label="ACTIVE_AGENTS">
          <div className="text-3xl font-heading font-black text-primary">{config.agent_count}</div>
        </div>

        <div className="panel" data-label="EST_MONTHLY_COST">
          <div className="text-3xl font-heading font-black text-primary">
            ${estimatedMonthlyCost.toFixed(2)}
          </div>
        </div>
      </div>

      <section className="panel" data-label="AGENT_SCALING">
        <p className="text-[10px] text-app-muted mb-6">
          Control how many agents can run in parallel. More agents = faster task execution but
          higher cost.
        </p>

        <div className="space-y-6">
          <div>
            <div className="flex justify-between mb-2">
              <label htmlFor="agentCount" className="text-[10px] font-heading text-app-muted">
                PARALLEL_AGENTS
              </label>
              <span className="text-[10px] font-heading text-text-main">
                {config.agent_count} / {config.max_agents}
              </span>
            </div>

            <input
              id="agentCount"
              type="range"
              min={config.min_agents}
              max={config.max_agents}
              value={config.agent_count}
              onChange={(e) =>
                setConfig({ ...config, agent_count: Number.parseInt(e.target.value, 10) })
              }
              className="w-full h-1 bg-panel-border appearance-none cursor-pointer accent-primary"
            />

            <div className="flex justify-between text-[10px] text-app-muted mt-2">
              <span>{config.min_agents} (min)</span>
              <span>{config.max_agents} (max)</span>
            </div>
          </div>

          <div className="border border-panel-border p-4 space-y-1.5 text-[10px]">
            <div className="font-heading text-text-main mb-2">PERFORMANCE_VS_COST</div>
            <div className="text-app-muted space-y-1">
              <div>
                <span className="text-text-main font-heading">1-3</span> — Budget-friendly, slower
                execution
              </div>
              <div>
                <span className="text-text-main font-heading">5-10</span> — Recommended balance for
                most teams
              </div>
              <div>
                <span className="text-text-main font-heading">15-20</span> — Maximum throughput,
                higher cost
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-panel-border">
            <button
              type="button"
              onClick={handleSave}
              disabled={saveMutation.isPending || isLoading}
              className="btn-primary text-[10px] font-heading disabled:opacity-50 flex items-center gap-2 ml-auto"
            >
              {saveMutation.isPending && <Loader size={12} className="animate-spin" />}
              APPLY_SCALING
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
