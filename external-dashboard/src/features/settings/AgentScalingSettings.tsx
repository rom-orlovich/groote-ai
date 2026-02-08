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
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Agent Scaling</h1>
        <p className="text-gray-600">
          Control how many agents can run in parallel. More agents = faster task execution but
          higher cost.
        </p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-lg flex items-start gap-3 ${
            message.type === "success"
              ? "bg-green-50 text-green-800 border border-green-200"
              : "bg-red-50 text-red-800 border border-red-200"
          }`}
        >
          {message.type === "success" ? (
            <CheckCircle size={20} className="flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Active Agents</div>
          <div className="text-3xl font-bold text-blue-600">{config.agent_count}</div>
        </div>

        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Est. Monthly Cost</div>
          <div className="text-3xl font-bold text-blue-600">${estimatedMonthlyCost.toFixed(2)}</div>
        </div>
      </div>

      <div className="bg-white border rounded-lg p-6 space-y-6">
        <div>
          <div className="flex justify-between mb-2">
            <label htmlFor="agentCount" className="text-sm font-medium text-gray-700">
              Number of Parallel Agents
            </label>
            <span className="text-sm text-gray-600">
              {config.agent_count} of {config.max_agents}
            </span>
          </div>

          <input
            id="agentCount"
            type="range"
            min={config.min_agents}
            max={config.max_agents}
            value={config.agent_count}
            onChange={(e) => setConfig({ ...config, agent_count: parseInt(e.target.value, 10) })}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />

          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span>{config.min_agents} (minimum)</span>
            <span>{config.max_agents} (maximum)</span>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded p-4 space-y-2 text-sm">
          <div className="font-semibold text-blue-900">Performance vs Cost</div>
          <div className="text-blue-800 space-y-1">
            <div>
              • <strong>1-3 agents:</strong> Budget-friendly, slower execution
            </div>
            <div>
              • <strong>5-10 agents:</strong> Recommended balance for most teams
            </div>
            <div>
              • <strong>15-20 agents:</strong> Maximum throughput, higher cost
            </div>
          </div>
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={handleSave}
            disabled={saveMutation.isPending || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition disabled:opacity-50 font-medium flex items-center gap-2 ml-auto"
          >
            {saveMutation.isPending && <Loader size={16} className="animate-spin" />}
            Apply Scaling
          </button>
        </div>
      </div>
    </div>
  );
}
