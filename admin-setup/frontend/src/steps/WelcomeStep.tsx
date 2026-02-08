import { CheckCircle, Loader2, XCircle } from "lucide-react";
import { useInfrastructure, useSaveStep } from "../hooks/useSetup";

interface WelcomeStepProps {
  onNext: () => void;
}

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  const { data, isLoading, refetch } = useInfrastructure();
  const saveMutation = useSaveStep();

  const allHealthy = data?.postgres.healthy && data?.redis.healthy;

  const handleBegin = () => {
    saveMutation.mutate({ stepId: "welcome", data: { configs: {} } }, { onSuccess: onNext });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-heading mb-2">INFRASTRUCTURE_CHECK</h2>
        <p className="text-[11px] text-gray-400">
          Verifying database and cache connectivity before proceeding with setup.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <HealthCard label="POSTGRESQL" status={data?.postgres} isLoading={isLoading} />
        <HealthCard label="REDIS" status={data?.redis} isLoading={isLoading} />
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => refetch()}
          className="px-4 py-2 text-[10px] font-heading border border-panel-border text-gray-400 hover:border-primary hover:text-primary transition-colors"
        >
          RECHECK
        </button>
        {allHealthy && (
          <button
            type="button"
            onClick={handleBegin}
            disabled={saveMutation.isPending}
            className="btn-primary text-[10px] disabled:opacity-50"
          >
            {saveMutation.isPending ? "STARTING..." : "BEGIN_SETUP"}
          </button>
        )}
      </div>
    </div>
  );
}

function HealthCard({
  label,
  status,
  isLoading,
}: {
  label: string;
  status: { healthy: boolean; message: string } | undefined;
  isLoading: boolean;
}) {
  return (
    <div className="panel" data-label={label}>
      <div className="flex items-center gap-3">
        {isLoading ? (
          <Loader2 size={16} className="animate-spin text-primary" />
        ) : status?.healthy ? (
          <CheckCircle size={16} className="text-green-500" />
        ) : (
          <XCircle size={16} className="text-red-500" />
        )}
        <div>
          <p className="text-[11px] font-heading">
            {isLoading ? "CHECKING..." : status?.healthy ? "CONNECTED" : "DISCONNECTED"}
          </p>
          {status?.message && !isLoading && (
            <p className="text-[9px] text-gray-500 mt-0.5">{status.message}</p>
          )}
        </div>
      </div>
    </div>
  );
}
