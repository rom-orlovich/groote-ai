import {
  AlertTriangle,
  Check,
  ClipboardList,
  Github,
  Link2,
  MessageSquare,
  Webhook,
  X,
} from "lucide-react";
import type { OAuthStatus } from "./hooks/useOAuthStatus";

interface IntegrationCardProps {
  status: OAuthStatus;
  onConnect: () => void;
  onDisconnect: () => void;
  isConnecting: boolean;
  isDisconnecting: boolean;
}

const PLATFORM_ICONS: Record<string, React.ReactNode> = {
  github: <Github size={24} />,
  jira: <ClipboardList size={24} />,
  slack: <MessageSquare size={24} />,
  sentry: <AlertTriangle size={24} />,
};

const MANUAL_WEBHOOK_PLATFORMS = ["slack"];

function WebhookStatusBadge({ status }: { status: OAuthStatus }) {
  if (status.webhook_registered) {
    return (
      <div className="mb-4 flex items-center gap-1.5 px-2 py-1 text-[10px] font-heading border border-green-200 dark:border-green-800 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/30 w-fit">
        <Webhook size={10} />
        WEBHOOK_ACTIVE
      </div>
    );
  }

  if (MANUAL_WEBHOOK_PLATFORMS.includes(status.platform)) {
    return (
      <div className="mb-4 flex items-center gap-1.5 px-2 py-1 text-[10px] font-heading border border-yellow-200 dark:border-yellow-800 text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-950/30 w-fit">
        <AlertTriangle size={10} />
        MANUAL_WEBHOOK_SETUP_REQUIRED
      </div>
    );
  }

  if (status.webhook_error) {
    return (
      <div className="mb-4 flex items-center gap-1.5 px-2 py-1 text-[10px] font-heading border border-yellow-200 dark:border-yellow-800 text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-950/30 w-fit">
        <AlertTriangle size={10} />
        WEBHOOK_SETUP_FAILED
      </div>
    );
  }

  return null;
}

export function IntegrationCard({
  status,
  onConnect,
  onDisconnect,
  isConnecting,
  isDisconnecting,
}: IntegrationCardProps) {
  const icon = PLATFORM_ICONS[status.platform] || <Link2 size={24} />;
  const isLoading = isConnecting || isDisconnecting;

  return (
    <div className="p-6 border border-panel-border hover:border-primary transition-colors bg-panel-bg">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="text-app-muted">{icon}</div>
          <div>
            <h3 className="text-sm font-heading font-bold text-text-main">{status.name}</h3>
            <p className="text-[10px] text-app-muted">{status.description}</p>
          </div>
        </div>
        <div
          className={`flex items-center gap-1 px-2 py-1 text-[10px] font-heading border ${
            status.connected
              ? "border-green-200 dark:border-green-800 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/30"
              : status.configured
                ? "border-yellow-200 dark:border-yellow-800 text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-950/30"
                : "border-panel-border text-app-muted bg-panel-border/20"
          }`}
        >
          {status.connected ? (
            <>
              <Check size={10} />
              CONNECTED
            </>
          ) : status.configured ? (
            <>
              <X size={10} />
              DISCONNECTED
            </>
          ) : (
            "NOT_CONFIGURED"
          )}
        </div>
      </div>

      {status.connected && status.installed_at && (
        <div className="mb-4 text-[10px] text-app-muted">
          Connected: {new Date(status.installed_at).toLocaleDateString()}
          {status.scopes && status.scopes.length > 0 && (
            <span className="ml-2">
              Scopes: {status.scopes.slice(0, 3).join(", ")}
              {status.scopes.length > 3 && ` +${status.scopes.length - 3} more`}
            </span>
          )}
        </div>
      )}

      {status.connected && <WebhookStatusBadge status={status} />}

      <div className="flex gap-2">
        {status.connected ? (
          <button
            type="button"
            onClick={onDisconnect}
            disabled={isLoading}
            className="flex-1 px-4 py-2 text-[10px] font-heading border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors disabled:opacity-50"
          >
            {isDisconnecting ? "DISCONNECTING..." : "DISCONNECT"}
          </button>
        ) : (
          <button
            type="button"
            onClick={onConnect}
            disabled={isLoading || !status.configured}
            className="flex-1 px-4 py-2 text-[10px] font-heading border border-primary text-primary hover:bg-primary hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isConnecting ? "CONNECTING..." : status.configured ? "CONNECT" : "NOT_CONFIGURED"}
          </button>
        )}
      </div>

      {!status.configured && (
        <p className="mt-2 text-[10px] text-red-400">
          Missing environment variables. Check server configuration.
        </p>
      )}
    </div>
  );
}
