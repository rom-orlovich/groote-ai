import { CheckCircle, Loader2, RefreshCw, XCircle } from "lucide-react";
import { useEffect } from "react";
import { SETUP_STEPS } from "../constants";
import { useInfrastructure } from "../hooks/useSetup";
import type { InfrastructureStatus } from "../types";

const overviewSteps = SETUP_STEPS.filter((s) => s.id !== "welcome" && s.id !== "review").map(
  (s, i) => ({
    number: String(i + 1).padStart(2, "0"),
    label: `${s.title} - ${s.description}${s.skippable ? " (optional)" : ""}`,
  }),
);

interface WelcomeStepProps {
  onNext: () => void;
  isReconfiguring?: boolean;
}

function StatusIcon({ healthy }: { healthy: boolean | undefined }) {
  if (healthy === undefined) return <Loader2 size={14} className="animate-spin text-gray-400" />;
  if (healthy) return <CheckCircle size={14} className="text-green-500" />;
  return <XCircle size={14} className="text-red-500" />;
}

function InfraRow({
  label,
  status,
}: {
  label: string;
  status: { healthy: boolean; message: string } | undefined;
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800">
      <span className="text-[10px] font-heading">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-gray-500 font-mono">
          {status?.message || "Checking..."}
        </span>
        <StatusIcon healthy={status?.healthy} />
      </div>
    </div>
  );
}

export function WelcomeStep({ onNext, isReconfiguring = false }: WelcomeStepProps) {
  const { data, isLoading, refetch, isFetching } = useInfrastructure();

  useEffect(() => {
    refetch();
  }, [refetch]);

  const infra = data as InfrastructureStatus | undefined;
  const allHealthy = infra?.postgres?.healthy && infra?.redis?.healthy;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-heading font-black tracking-wider mb-2">
          {isReconfiguring ? "RECONFIGURE_SYSTEM" : "SYSTEM_INIT"}
        </h2>
        <p className="text-[10px] text-gray-500 font-mono leading-relaxed">
          {isReconfiguring
            ? "Review and update your existing configuration. Each integration can be modified or skipped."
            : "Configure Groote AI step by step. Each integration can be skipped and configured later. After setup, download the generated .env file and restart services."}
        </p>
      </div>

      <div className="panel" data-label="INFRASTRUCTURE_CHECK">
        <div className="flex justify-between items-center mb-4">
          <span className="text-[10px] font-heading text-gray-400">DEPENDENCY_STATUS</span>
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-1.5 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            <RefreshCw size={12} className={isFetching ? "animate-spin" : ""} />
          </button>
        </div>
        <InfraRow label="POSTGRESQL" status={infra?.postgres} />
        <InfraRow label="REDIS" status={infra?.redis} />
      </div>

      <div className="panel" data-label="SETUP_OVERVIEW">
        <div className="text-[10px] font-mono text-gray-600 dark:text-gray-400 space-y-2">
          {overviewSteps.map((step) => (
            <div key={step.number} className="flex items-center gap-2">
              <span className="text-orange-500 font-heading">{step.number}</span>
              <span>{step.label}</span>
            </div>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={onNext}
        disabled={isLoading || !allHealthy}
        className="w-full btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {isLoading
          ? "CHECKING..."
          : allHealthy
            ? isReconfiguring
              ? "CONTINUE_RECONFIGURE"
              : "BEGIN_SETUP"
            : "INFRASTRUCTURE_NOT_READY"}
      </button>
    </div>
  );
}
