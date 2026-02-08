import { Download, Loader2, RotateCcw } from "lucide-react";
import { useState } from "react";
import { STEPS } from "../constants";
import { useCompleteSetup, useExportConfig } from "../hooks/useSetup";

interface ReviewStepProps {
  completedSteps: string[];
  skippedSteps: string[];
}

export function ReviewStep({ completedSteps, skippedSteps }: ReviewStepProps) {
  const [envContent, setEnvContent] = useState<string | null>(null);
  const completeMutation = useCompleteSetup();
  const exportQuery = useExportConfig();

  const handleExport = async () => {
    const result = await exportQuery.refetch();
    if (result.data) {
      setEnvContent(result.data.content);
    }
  };

  const handleDownload = () => {
    if (!envContent) return;
    const blob = new Blob([envContent], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = ".env";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleComplete = () => {
    completeMutation.mutate();
  };

  const configuredSteps = STEPS.filter((s) => s.id !== "welcome" && s.id !== "review");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-heading mb-2">REVIEW_CONFIGURATION</h2>
        <p className="text-[11px] text-gray-400">
          Review your setup progress and export the configuration file.
        </p>
      </div>

      <div className="grid gap-3">
        {configuredSteps.map((step) => {
          const isCompleted = completedSteps.includes(step.id);
          const isSkipped = skippedSteps.includes(step.id);

          return (
            <div
              key={step.id}
              className="panel flex items-center justify-between"
              data-label={step.category.toUpperCase()}
            >
              <span className="text-[11px] font-heading">{step.title}</span>
              <span
                className={`text-[9px] font-heading px-2 py-0.5 border ${
                  isCompleted
                    ? "border-green-500/30 text-green-500 bg-green-500/10"
                    : isSkipped
                      ? "border-yellow-500/30 text-yellow-500 bg-yellow-500/10"
                      : "border-gray-500/30 text-gray-500"
                }`}
              >
                {isCompleted ? "CONFIGURED" : isSkipped ? "SKIPPED" : "PENDING"}
              </span>
            </div>
          );
        })}
      </div>

      {envContent && (
        <div className="panel" data-label="ENV_PREVIEW">
          <pre className="text-[10px] font-mono text-gray-400 whitespace-pre-wrap max-h-48 overflow-y-auto">
            {envContent}
          </pre>
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={handleExport}
          disabled={exportQuery.isFetching}
          className="px-4 py-2 text-[10px] font-heading border border-panel-border text-gray-400 hover:border-primary hover:text-primary transition-colors flex items-center gap-2 disabled:opacity-50"
        >
          {exportQuery.isFetching ? (
            <Loader2 size={12} className="animate-spin" />
          ) : (
            <RotateCcw size={12} />
          )}
          GENERATE_ENV
        </button>
        {envContent && (
          <button
            type="button"
            onClick={handleDownload}
            className="px-4 py-2 text-[10px] font-heading border border-primary text-primary hover:bg-primary/10 transition-colors flex items-center gap-2"
          >
            <Download size={12} />
            DOWNLOAD_.ENV
          </button>
        )}
        <button
          type="button"
          onClick={handleComplete}
          disabled={completeMutation.isPending || completeMutation.isSuccess}
          className="btn-primary text-[10px] disabled:opacity-50 flex items-center gap-2"
        >
          {completeMutation.isPending
            ? "COMPLETING..."
            : completeMutation.isSuccess
              ? "SETUP_COMPLETE"
              : "COMPLETE_SETUP"}
        </button>
      </div>

      {completeMutation.isSuccess && (
        <div className="panel border-green-500/30" data-label="STATUS">
          <p className="text-[11px] text-green-400 font-heading">
            SETUP_COMPLETE - Your configuration has been saved. Download the .env file and restart
            services.
          </p>
        </div>
      )}
    </div>
  );
}
