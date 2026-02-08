import { AlertCircle, CheckCircle, Loader } from "lucide-react";
import { useEffect, useState } from "react";
import { useAgentScalingConfig, useSaveAgentScaling } from "./hooks/useAgentScaling";
import { useAIProviderSettings, useSaveAIProvider } from "./hooks/useAIProviderSettings";

export function AIProviderSettings() {
  const [provider, setProvider] = useState("claude");
  const [agentCount, setAgentCount] = useState(5);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const { data: providerData } = useAIProviderSettings();
  const { data: scalingData, isLoading: scalingLoading } = useAgentScalingConfig();
  const saveProvider = useSaveAIProvider();
  const saveScaling = useSaveAgentScaling();

  useEffect(() => {
    if (providerData?.provider) {
      setProvider(providerData.provider);
    }
  }, [providerData]);

  useEffect(() => {
    if (scalingData?.agent_count) {
      setAgentCount(scalingData.agent_count);
    }
  }, [scalingData]);

  useEffect(() => {
    if (saveProvider.isSuccess && saveScaling.isSuccess) {
      setMessage({ type: "success", text: "Settings applied — scaling agents..." });
      setTimeout(() => setMessage(null), 3000);
    }
  }, [saveProvider.isSuccess, saveScaling.isSuccess]);

  useEffect(() => {
    if (saveProvider.isError || saveScaling.isError) {
      setMessage({ type: "error", text: "Failed to save settings" });
    }
  }, [saveProvider.isError, saveScaling.isError]);

  const handleSave = () => {
    saveProvider.mutate({ provider });
    saveScaling.mutate(agentCount);
  };

  const isSaving = saveProvider.isPending || saveScaling.isPending;
  const maxAgents = scalingData?.max_agents ?? 20;
  const minAgents = scalingData?.min_agents ?? 1;
  const costPerAgent = 0.05;
  const estimatedMonthlyCost = agentCount * costPerAgent * 730;

  if (scalingLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-app-muted font-heading">LOADING_SETTINGS...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
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

      <div className="grid grid-cols-3 gap-4">
        <div className="panel" data-label="PROVIDER">
          <div className="text-xl font-heading font-black text-primary uppercase">{provider}</div>
        </div>
        <div className="panel" data-label="ACTIVE_AGENTS">
          <div className="text-xl font-heading font-black text-primary">{agentCount}</div>
        </div>
        <div className="panel" data-label="EST_MONTHLY_COST">
          <div className="text-xl font-heading font-black text-primary">
            ${estimatedMonthlyCost.toFixed(2)}
          </div>
        </div>
      </div>

      <section className="panel" data-label="CLI_PROVIDER">
        <div className="space-y-4">
          <p className="text-[10px] text-app-muted">
            Select which CLI provider the agent engine uses for task execution. API keys are
            configured via the .env file.
          </p>

          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setProvider("claude")}
              className={`p-4 border text-left transition-colors ${
                provider === "claude"
                  ? "border-primary bg-primary/5 dark:bg-primary/10"
                  : "border-panel-border hover:border-primary/50"
              }`}
            >
              <div className="text-sm font-heading font-black mb-1">CLAUDE</div>
              <div className="text-[10px] text-app-muted">Anthropic CLI</div>
            </button>

            <button
              type="button"
              onClick={() => setProvider("cursor")}
              className={`p-4 border text-left transition-colors ${
                provider === "cursor"
                  ? "border-primary bg-primary/5 dark:bg-primary/10"
                  : "border-panel-border hover:border-primary/50"
              }`}
            >
              <div className="text-sm font-heading font-black mb-1">CURSOR</div>
              <div className="text-[10px] text-app-muted">Cursor AI CLI</div>
            </button>
          </div>
        </div>
      </section>

      <section className="panel" data-label="AGENT_SCALING">
        <div className="space-y-6">
          <p className="text-[10px] text-app-muted">
            Control how many agents can run in parallel. More agents = faster task execution but
            higher cost.
          </p>

          <div>
            <div className="flex justify-between mb-2">
              <label htmlFor="agentCount" className="text-[10px] font-heading text-app-muted">
                PARALLEL_AGENTS
              </label>
              <span className="text-[10px] font-heading text-text-main">
                {agentCount} / {maxAgents}
              </span>
            </div>

            <input
              id="agentCount"
              type="range"
              min={minAgents}
              max={maxAgents}
              value={agentCount}
              onChange={(e) => setAgentCount(Number.parseInt(e.target.value, 10))}
              className="w-full h-1 bg-panel-border appearance-none cursor-pointer accent-primary"
            />

            <div className="flex justify-between text-[10px] text-app-muted mt-2">
              <span>{minAgents} (min)</span>
              <span>{maxAgents} (max)</span>
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
              disabled={isSaving}
              className="btn-primary text-[10px] font-heading disabled:opacity-50 flex items-center gap-2 ml-auto"
            >
              {isSaving && <Loader size={12} className="animate-spin" />}
              APPLY_SETTINGS
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
