import { CheckCircle, Download, Loader2, RotateCcw, SkipForward } from "lucide-react";
import { useState } from "react";
import { SETUP_STEPS } from "../constants";
import { useCompleteSetup, useExportConfig } from "../hooks/useSetup";
import type { ExportFormat, SetupStatus } from "../types";

interface ReviewStepProps {
  status: SetupStatus;
  onComplete: () => void;
}

const EXPORT_OPTIONS: { value: ExportFormat; label: string; description: string }[] = [
  { value: "env", label: ".ENV_FILE", description: "Docker Compose / local development" },
  { value: "k8s", label: "K8S_SECRET", description: "Kubernetes Secret YAML manifest" },
  { value: "docker-secrets", label: "DOCKER_SECRETS", description: "Docker Swarm secrets script" },
  { value: "github-actions", label: "GITHUB_ACTIONS", description: "GitHub Actions secrets guide" },
];

const FILENAMES: Record<ExportFormat, string> = {
  env: ".env",
  k8s: "groote-ai-secret.yaml",
  "docker-secrets": "create-secrets.sh",
  "github-actions": "github-actions-secrets.txt",
};

export function ReviewStep({ status, onComplete }: ReviewStepProps) {
  const completeSetup = useCompleteSetup();
  const exportConfig = useExportConfig();
  const [exportFormat, setExportFormat] = useState<ExportFormat>(status.is_cloud ? "k8s" : "env");

  const handleExport = () => {
    exportConfig.mutate(exportFormat, {
      onSuccess: (content) => {
        const blob = new Blob([content], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = FILENAMES[exportFormat];
        a.click();
        URL.revokeObjectURL(url);
      },
    });
  };

  const handleComplete = () => {
    completeSetup.mutate(undefined, { onSuccess: () => onComplete() });
  };

  const configuredSteps = SETUP_STEPS.filter((s) => s.id !== "welcome" && s.id !== "review");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-heading font-black tracking-wider mb-2">REVIEW</h2>
        <p className="text-[10px] text-gray-500 font-mono">
          Review configuration and export for your deployment target.
        </p>
        {status.is_cloud && (
          <p className="text-[9px] font-heading text-blue-400 mt-1">
            CLOUD_MODE: {status.deployment_mode.toUpperCase()}
          </p>
        )}
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
                <span className="text-[10px] font-heading">{step.title}</span>
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

      <div className="panel" data-label="EXPORT_FORMAT">
        <div className="space-y-2">
          {EXPORT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setExportFormat(opt.value)}
              className={`w-full text-left p-2.5 border transition-colors ${
                exportFormat === opt.value
                  ? "border-orange-400 bg-orange-50 dark:bg-orange-900/20"
                  : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
              }`}
            >
              <div className="text-[10px] font-heading">{opt.label}</div>
              <div className="text-[9px] font-mono text-gray-500">{opt.description}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="panel" data-label="NEXT_STEPS">
        <div className="text-[10px] font-mono text-gray-600 dark:text-gray-400 space-y-3">
          {exportFormat === "env" && (
            <>
              <div className="flex gap-2">
                <span className="text-orange-500 font-heading shrink-0">1.</span>
                <span>Download the .env file</span>
              </div>
              <div className="flex gap-2">
                <span className="text-orange-500 font-heading shrink-0">2.</span>
                <span>Save to project root (replace existing .env)</span>
              </div>
              <div className="flex gap-2">
                <span className="text-orange-500 font-heading shrink-0">3.</span>
                <span>
                  Run{" "}
                  <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5">
                    docker compose up -d
                  </code>
                </span>
              </div>
            </>
          )}
          {exportFormat === "k8s" && (
            <>
              <div className="flex gap-2">
                <span className="text-orange-500 font-heading shrink-0">1.</span>
                <span>Download the K8s Secret YAML</span>
              </div>
              <div className="flex gap-2">
                <span className="text-orange-500 font-heading shrink-0">2.</span>
                <span>
                  Apply:{" "}
                  <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5">
                    kubectl apply -f groote-ai-secret.yaml
                  </code>
                </span>
              </div>
              <div className="flex gap-2">
                <span className="text-orange-500 font-heading shrink-0">3.</span>
                <span>Reference in your Deployment spec envFrom</span>
              </div>
            </>
          )}
          {exportFormat === "docker-secrets" && (
            <>
              <div className="flex gap-2">
                <span className="text-orange-500 font-heading shrink-0">1.</span>
                <span>Download the script</span>
              </div>
              <div className="flex gap-2">
                <span className="text-orange-500 font-heading shrink-0">2.</span>
                <span>
                  Run:{" "}
                  <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5">
                    bash create-secrets.sh
                  </code>
                </span>
              </div>
            </>
          )}
          {exportFormat === "github-actions" && (
            <>
              <div className="flex gap-2">
                <span className="text-orange-500 font-heading shrink-0">1.</span>
                <span>Download the secrets guide</span>
              </div>
              <div className="flex gap-2">
                <span className="text-orange-500 font-heading shrink-0">2.</span>
                <span>Add each secret in GitHub repo Settings</span>
              </div>
            </>
          )}
        </div>
      </div>

      <button
        type="button"
        onClick={handleExport}
        disabled={exportConfig.isPending}
        className="w-full py-2.5 text-[10px] font-heading border border-orange-400 text-orange-500 hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors flex items-center justify-center gap-2"
      >
        {exportConfig.isPending ? (
          <Loader2 size={12} className="animate-spin" />
        ) : (
          <Download size={12} />
        )}
        EXPORT_{exportFormat.toUpperCase().replace("-", "_")}
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
