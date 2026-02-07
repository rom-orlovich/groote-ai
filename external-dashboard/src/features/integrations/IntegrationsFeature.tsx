import { CheckCircle, RefreshCw, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useOAuthStatus } from "./hooks/useOAuthStatus";
import { IntegrationCard } from "./IntegrationCard";

const PLATFORM_ORDER = ["github", "jira", "slack", "sentry"];

interface CallbackNotification {
  platform: string;
  success: boolean;
  error?: string;
  webhookStatus?: "ok" | "failed";
}

export function IntegrationsFeature() {
  const {
    statuses,
    isLoading,
    isError,
    error,
    refetch,
    revoke,
    isRevoking,
    install,
    isInstalling,
  } = useOAuthStatus();

  const [notification, setNotification] = useState<CallbackNotification | null>(null);

  const handleOAuthCallback = useCallback(() => {
    const params = new URLSearchParams(window.location.search);
    const platform = params.get("oauth_callback");
    if (!platform) return;

    const success = params.get("success") === "true";
    const callbackError = params.get("error");
    const webhook = params.get("webhook") as "ok" | "failed" | null;

    setNotification({
      platform,
      success,
      error: callbackError ?? undefined,
      webhookStatus: webhook ?? undefined,
    });

    const url = new URL(window.location.href);
    url.searchParams.delete("oauth_callback");
    url.searchParams.delete("success");
    url.searchParams.delete("error");
    url.searchParams.delete("webhook");
    window.history.replaceState({}, "", url.pathname);

    refetch();

    setTimeout(() => setNotification(null), 5000);
  }, [refetch]);

  useEffect(() => {
    handleOAuthCallback();
  }, [handleOAuthCallback]);

  if (isLoading) {
    return <div className="p-8 text-center font-heading">LOADING_INTEGRATIONS...</div>;
  }

  if (isError) {
    return (
      <div className="p-8 text-center">
        <div className="text-red-500 font-heading mb-4">
          ERROR: {error instanceof Error ? error.message : "Failed to load integrations"}
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          className="px-4 py-2 border border-gray-200 hover:bg-gray-50 text-[10px] font-heading"
        >
          RETRY
        </button>
      </div>
    );
  }

  const orderedStatuses = PLATFORM_ORDER.map((platform) => statuses?.[platform]).filter(Boolean);

  const connectedCount = orderedStatuses.filter((s) => s?.connected).length;
  const configuredCount = orderedStatuses.filter((s) => s?.configured).length;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {notification && (
        <div
          className={`flex items-center gap-3 p-4 border text-[10px] font-heading ${
            notification.success
              ? "border-green-200 bg-green-50 text-green-700"
              : "border-red-200 bg-red-50 text-red-700"
          }`}
        >
          {notification.success ? <CheckCircle size={14} /> : <XCircle size={14} />}
          <span>
            {notification.success
              ? `${notification.platform.toUpperCase()} connected successfully${notification.webhookStatus === "ok" ? " - webhook configured" : notification.webhookStatus === "failed" ? " - webhook setup failed" : ""}`
              : `${notification.platform.toUpperCase()} connection failed${notification.error ? `: ${notification.error}` : ""}`}
          </span>
        </div>
      )}

      <section className="panel" data-label="INTEGRATIONS">
        <div className="flex justify-between items-center mb-6">
          <div className="flex gap-8">
            <div className="stat-mini">
              <div className="text-[10px] font-heading text-gray-400">CONNECTED</div>
              <div className="text-xl font-heading font-black text-green-500">{connectedCount}</div>
            </div>
            <div className="stat-mini">
              <div className="text-[10px] font-heading text-gray-400">CONFIGURED</div>
              <div className="text-xl font-heading font-black">{configuredCount}</div>
            </div>
            <div className="stat-mini">
              <div className="text-[10px] font-heading text-gray-400">TOTAL</div>
              <div className="text-xl font-heading font-black">{PLATFORM_ORDER.length}</div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => refetch()}
            className="p-2 border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <RefreshCw size={14} />
          </button>
        </div>

        <p className="text-[10px] text-gray-400 mb-6">
          Connect your external services to enable webhook integrations and automated workflows.
          OAuth connections allow the agent to interact with these services on your behalf.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {orderedStatuses.map(
            (status) =>
              status && (
                <IntegrationCard
                  key={status.platform}
                  status={status}
                  onConnect={() => install(status.platform)}
                  onDisconnect={() => revoke(status.platform)}
                  isConnecting={isInstalling}
                  isDisconnecting={isRevoking}
                />
              ),
          )}
        </div>
      </section>
    </div>
  );
}
