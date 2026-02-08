import type { ConfigSummaryItem } from "../types";

interface ConfigSummaryProps {
  title: string;
  status: "configured" | "skipped";
  configs: ConfigSummaryItem[];
}

export function ConfigSummary({ title, status, configs }: ConfigSummaryProps) {
  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-heading text-[11px] text-primary">{title}</h3>
        {status === "configured" ? (
          <span className="text-[9px] px-2 py-0.5 bg-green-500/20 text-green-500 border border-green-500/30">
            CONFIGURED
          </span>
        ) : (
          <span className="text-[9px] px-2 py-0.5 bg-yellow-500/20 text-yellow-500 border border-yellow-500/30">
            SKIPPED
          </span>
        )}
      </div>
      {status === "configured" && configs.length > 0 && (
        <div className="space-y-1">
          {configs.map((config) => (
            <div key={config.key} className="flex justify-between text-[9px]">
              <span className="text-gray-500 font-mono">{config.key}</span>
              <span className="text-gray-300 font-mono">{config.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
