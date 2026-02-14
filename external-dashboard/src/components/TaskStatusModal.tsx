import { clsx } from "clsx";
import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useFullTaskLogs } from "../features/overview/hooks/useTaskLogs";
import { useTaskModal } from "../hooks/useTaskModal";
import { AgentOutputTab, FinalResultTab, KnowledgeTab, WebhookFlowTab } from "./TaskModalTabs";

type TabKey = "agent" | "webhook" | "knowledge" | "result";

export function TaskStatusModal() {
  const { isOpen, taskId, closeTask } = useTaskModal();
  const { data: logs, isLoading } = useFullTaskLogs(taskId);
  const logEndRef = useRef<HTMLDivElement>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("agent");

  const agentOutput = logs?.agent_output;
  useEffect(() => {
    if (agentOutput?.length && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [agentOutput]);

  useEffect(() => {
    if (isOpen) setActiveTab("agent");
  }, [isOpen]);

  if (!isOpen || !taskId) return null;

  const status = logs?.metadata?.status || "queued";
  const isLive = status === "running" || status === "queued";

  const tabs: { key: TabKey; label: string; count?: number }[] = [
    { key: "agent", label: "AGENT_OUTPUT", count: logs?.agent_output?.length },
    { key: "webhook", label: "WEBHOOK_FLOW", count: logs?.webhook_flow?.length },
    { key: "knowledge", label: "KNOWLEDGE", count: logs?.knowledge_interactions?.length },
    { key: "result", label: "FINAL_RESULT", count: logs?.final_result ? 1 : 0 },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-[2px] animate-in fade-in duration-200">
      <div className="bg-modal-bg rounded-lg shadow-2xl w-full max-w-3xl mx-4 overflow-hidden border border-modal-border animate-in zoom-in-95 duration-200 ring-1 ring-black/5">
        <div className="flex items-center justify-between p-4 border-b border-modal-border bg-background-app/80">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${getStatusColor(status)}`} />
            <h3 className="font-heading font-bold text-xs uppercase tracking-wider text-app-main">
              TASK_DETAILS: {taskId}
            </h3>
            {isLive && (
              <span className="text-blue-500 animate-pulse text-[8px] font-bold ml-2">LIVE</span>
            )}
          </div>
          <button
            type="button"
            onClick={closeTask}
            className="p-1 hover:bg-gray-200 dark:hover:bg-slate-800 rounded text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {logs?.metadata && (
          <div className="px-4 py-3 border-b border-modal-border bg-background-app/30 grid grid-cols-2 md:grid-cols-5 gap-3">
            <MetadataField label="TASK_ID" value={taskId} />
            <MetadataField label="AGENT" value={String(logs.metadata.assigned_agent || "brain")} />
            <MetadataField label="STATUS" value={logs.metadata.status || "queued"} />
            <MetadataField
              label="COST"
              value={logs.metadata.cost_usd ? `$${Number(logs.metadata.cost_usd).toFixed(4)}` : "-"}
            />
            <MetadataField
              label="STARTED"
              value={
                logs.metadata.created_at
                  ? new Date(logs.metadata.created_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })
                  : "-"
              }
            />
          </div>
        )}

        <div className="flex border-b border-modal-border bg-background-app/40">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={clsx(
                "px-4 py-2 text-[9px] font-heading font-bold uppercase tracking-wider transition-colors border-b-2",
                activeTab === tab.key
                  ? "text-primary border-primary bg-panel-bg/50"
                  : "text-app-muted border-transparent hover:text-app-main hover:bg-panel-bg/30",
              )}
            >
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span className="ml-1.5 text-[8px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="p-4">
          <div className="rounded bg-slate-950 p-4 font-mono text-[10px] text-gray-300 overflow-y-auto max-h-[60vh] border border-slate-800 shadow-inner">
            {isLoading ? (
              <div className="text-gray-600 animate-pulse">CONNECTING_TO_STREAM...</div>
            ) : (
              <>
                {activeTab === "agent" && <AgentOutputTab entries={logs?.agent_output} />}
                {activeTab === "webhook" && <WebhookFlowTab events={logs?.webhook_flow} />}
                {activeTab === "knowledge" && (
                  <KnowledgeTab interactions={logs?.knowledge_interactions} />
                )}
                {activeTab === "result" && <FinalResultTab result={logs?.final_result} />}
                <div ref={logEndRef} />
              </>
            )}
          </div>
        </div>

        <div className="p-4 bg-background-app/50 border-t border-modal-border flex justify-end gap-2">
          <button
            type="button"
            onClick={closeTask}
            className="px-4 py-2 bg-panel-bg border border-input-border text-[10px] font-heading font-bold hover:bg-background-app text-app-main transition-colors rounded shadow-sm hover:shadow"
          >
            CLOSE_PANEL
          </button>
        </div>
      </div>
    </div>
  );
}

function getStatusColor(status: string) {
  switch (status) {
    case "completed":
      return "bg-green-500";
    case "running":
      return "bg-blue-500 animate-pulse";
    case "failed":
      return "bg-red-500";
    default:
      return "bg-gray-300";
  }
}

function MetadataField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[8px] font-heading font-bold text-app-muted tracking-wider uppercase">
        {label}
      </div>
      <div className="text-[10px] font-mono text-app-main truncate">{value}</div>
    </div>
  );
}
