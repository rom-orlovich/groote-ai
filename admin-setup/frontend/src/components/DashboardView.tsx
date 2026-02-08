import { CheckCircle, Clipboard, Download, Pencil, RotateCcw } from "lucide-react";
import { useState } from "react";
import { STEPS } from "../constants";
import { useConfigSummary, useExportConfig } from "../hooks/useSetup";
import type { ConfigSummaryItem } from "../types";
import { ConfigSummary } from "./ServiceCard";

interface DashboardViewProps {
  completedSteps: string[];
  skippedSteps: string[];
  onResetSetup: () => void;
  onEditConfiguration: () => void;
}

const CATEGORY_BY_STEP: Record<string, string> = {
  public_url: "domain",
  github: "github",
  jira: "jira",
  slack: "slack",
};

function groupByStep(configs: ConfigSummaryItem[]): Record<string, ConfigSummaryItem[]> {
  const grouped: Record<string, ConfigSummaryItem[]> = {};
  for (const config of configs) {
    const stepId = Object.entries(CATEGORY_BY_STEP).find(([, cat]) => cat === config.category)?.[0];
    if (stepId) {
      if (!grouped[stepId]) grouped[stepId] = [];
      grouped[stepId].push(config);
    }
  }
  return grouped;
}

export function DashboardView({
  completedSteps,
  skippedSteps,
  onResetSetup,
  onEditConfiguration,
}: DashboardViewProps) {
  const [copied, setCopied] = useState(false);
  const exportQuery = useExportConfig();
  const summaryQuery = useConfigSummary();

  const serviceSteps = STEPS.filter((step) => step.id !== "welcome" && step.id !== "review");
  const configsByStep = groupByStep(summaryQuery.data || []);

  const handleExportEnv = async () => {
    const result = await exportQuery.refetch();
    if (!result.data?.content) return;
    const blob = new Blob([result.data.content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = ".env";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleCopyClipboard = async () => {
    const result = await exportQuery.refetch();
    if (!result.data?.content) return;
    await navigator.clipboard.writeText(result.data.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <CheckCircle className="w-10 h-10 text-green-500 mx-auto" />
        <h1 className="font-heading text-primary text-xl">SETUP_COMPLETE</h1>
        <p className="text-[11px] text-gray-400">All services have been configured</p>
      </div>

      <div className="grid gap-3">
        {serviceSteps.map((step) => {
          const isConfigured = completedSteps.includes(step.id);
          const isSkipped = skippedSteps.includes(step.id);
          if (!isConfigured && !isSkipped) return null;
          return (
            <ConfigSummary
              key={step.id}
              title={step.title}
              status={isConfigured ? "configured" : "skipped"}
              configs={configsByStep[step.id] || []}
            />
          );
        })}
      </div>

      <div className="panel p-4 space-y-4">
        <h2 className="font-heading text-[11px] text-primary">EXPORT_CONFIGURATION</h2>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleExportEnv}
            className="btn-primary flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            <span className="text-[10px]">EXPORT_.ENV</span>
          </button>
          <button
            type="button"
            onClick={handleCopyClipboard}
            className="btn-primary flex items-center gap-2 bg-gray-600 hover:bg-gray-500"
          >
            <Clipboard className="w-4 h-4" />
            <span className="text-[10px]">{copied ? "COPIED" : "COPY_TO_CLIPBOARD"}</span>
          </button>
        </div>
        {exportQuery.data?.content && (
          <pre className="bg-black/20 rounded p-3 text-[9px] text-gray-300 overflow-x-auto max-h-48">
            {exportQuery.data.content}
          </pre>
        )}
      </div>

      <div className="panel p-4 space-y-3">
        <h2 className="font-heading text-[11px] text-primary">NEXT_STEPS</h2>
        <ol className="space-y-2 text-[10px] text-gray-300 list-decimal list-inside">
          <li>
            Place the <span className="font-mono text-primary">.env</span> file in your project root
          </li>
          <li>
            Run <span className="font-mono text-primary">make up</span> to start all services
          </li>
          <li>
            Visit your <span className="font-mono text-primary">PUBLIC_URL</span> to access the
            dashboard
          </li>
        </ol>
      </div>

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onEditConfiguration}
          className="btn-primary flex items-center gap-2 bg-gray-600 hover:bg-gray-500"
        >
          <Pencil className="w-3 h-3" />
          <span className="text-[10px]">EDIT_CONFIGURATION</span>
        </button>
        <button
          type="button"
          onClick={onResetSetup}
          className="flex items-center gap-2 text-[10px] text-red-400 hover:text-red-300 transition-colors"
        >
          <RotateCcw className="w-3 h-3" />
          <span>RESET_SETUP</span>
        </button>
      </div>
    </div>
  );
}
