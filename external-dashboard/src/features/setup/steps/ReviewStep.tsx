import { CheckCircle, Download, Loader2, RotateCcw, SkipForward } from "lucide-react";
import { useCompleteSetup, useExportEnv } from "../hooks/useSetup";
import type { SetupStatus } from "../types";
import { SETUP_STEPS } from "../constants";

interface ReviewStepProps {
  status: SetupStatus;
  onComplete: () => void;
}

export function ReviewStep({ status, onComplete }: ReviewStepProps) {
  const completeSetup = useCompleteSetup();
  const exportEnv = useExportEnv();

  const handleExport = () => {
    exportEnv.mutate(undefined, {
      onSuccess: (content) => {
        const blob = new Blob([content], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = ".env";
        a.click();
        URL.revokeObjectURL(url);
      },
    });
  };

  const handleComplete = () => {
    completeSetup.mutate(undefined, { onSuccess: () => onComplete() });
  };

  const configuredSteps = SETUP_STEPS.filter(
    (s) => s.id !== "welcome" && s.id !== "review",
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-heading font-black tracking-wider mb-2">REVIEW</h2>
        <p className="text-[10px] text-gray-500 font-mono">
          Review your configuration. Download the .env file and restart services to activate.
        </p>
      </div>

      <div className="panel" data-label="CONFIGURATION_STATUS">
        <div className="space-y-2">
          {configuredSteps.map((step) => {
            const isCompleted = status.completed_steps.includes(step.id);
            const isSkipped = status.skipped_steps.includes(step.id);
            return (
              <div
                key={step.id}
                className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800"
              >
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-heading">{step.title}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  {isCompleted && (
                    <>
                      <CheckCircle size={12} className="text-green-500" />
                      <span className="text-[9px] font-heading text-green-500">CONFIGURED</span>
                    </>
                  )}
                  {isSkipped && (
                    <>
                      <SkipForward size={12} className="text-yellow-500" />
                      <span className="text-[9px] font-heading text-yellow-500">SKIPPED</span>
                    </>
                  )}
                  {!isCompleted && !isSkipped && (
                    <>
                      <RotateCcw size={12} className="text-gray-400" />
                      <span className="text-[9px] font-heading text-gray-400">PENDING</span>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="panel" data-label="NEXT_STEPS">
        <div className="text-[10px] font-mono text-gray-600 dark:text-gray-400 space-y-3">
          <div className="flex gap-2">
            <span className="text-orange-500 font-heading shrink-0">1.</span>
            <span>Download the .env file with your configuration</span>
          </div>
          <div className="flex gap-2">
            <span className="text-orange-500 font-heading shrink-0">2.</span>
            <span>Save it to your project root (replace existing .env)</span>
          </div>
          <div className="flex gap-2">
            <span className="text-orange-500 font-heading shrink-0">3.</span>
            <span>
              Run <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5">docker compose down && docker compose up -d</code> to restart with new config
            </span>
          </div>
          <div className="flex gap-2">
            <span className="text-orange-500 font-heading shrink-0">4.</span>
            <span>
              Verify with <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5">make health</code>
            </span>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={handleExport}
        disabled={exportEnv.isPending}
        className="w-full py-2.5 text-[10px] font-heading border border-orange-400 text-orange-500 hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors flex items-center justify-center gap-2"
      >
        {exportEnv.isPending ? (
          <Loader2 size={12} className="animate-spin" />
        ) : (
          <Download size={12} />
        )}
        DOWNLOAD_.ENV
      </button>

      <button
        type="button"
        onClick={handleComplete}
        disabled={completeSetup.isPending}
        className="w-full btn-primary disabled:opacity-40"
      >
        {completeSetup.isPending ? "COMPLETING..." : "COMPLETE_SETUP"}
      </button>
    </div>
  );
}
