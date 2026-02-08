import { AlertCircle, ExternalLink, GitBranch, Hash, MessageSquare, Plug } from "lucide-react";
import { type Platform, useDisconnectPlatform, usePlatforms } from "./hooks/usePlatforms";

const PLATFORM_META: Record<
  string,
  {
    icon: typeof GitBranch;
    description: string;
    accent: string;
    iconBg: string;
  }
> = {
  github: {
    icon: GitBranch,
    description: "Access repositories, issues, and pull requests",
    accent: "bg-purple-500",
    iconBg: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  },
  jira: {
    icon: MessageSquare,
    description: "Create and manage tickets with AI-Fix labels",
    accent: "bg-blue-500",
    iconBg: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  },
  slack: {
    icon: Hash,
    description: "Get notifications and respond to inquiries",
    accent: "bg-emerald-500",
    iconBg: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  },
};

export function InstallPage() {
  const { data, isLoading } = usePlatforms();
  const disconnectMutation = useDisconnectPlatform();

  const platforms = data?.platforms || [];

  const handleConnect = (platformId: string) => {
    window.location.href = `/oauth/callback/${platformId}`;
  };

  const handleDisconnect = (platformId: string) => {
    disconnectMutation.mutate(platformId);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-app-muted font-heading">LOADING_PLATFORMS...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl animate-in fade-in duration-500">
      <div className="mb-2">
        <h1 className="text-sm font-heading font-bold text-text-main mb-1">INTEGRATIONS</h1>
        <p className="text-[10px] text-app-muted">
          Connect your development tools to enable Groote AI to access your repositories, issues,
          and communications.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        {platforms.map((platform: Platform) => (
          <PlatformCard
            key={platform.id}
            platform={platform}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
          />
        ))}
      </div>
    </div>
  );
}

function PlatformCard({
  platform,
  onConnect,
  onDisconnect,
}: {
  platform: Platform;
  onConnect: (id: string) => void;
  onDisconnect: (id: string) => void;
}) {
  const meta = PLATFORM_META[platform.id] || PLATFORM_META.github;
  const Icon = meta.icon;
  const isConnected = platform.configured && platform.connected;
  const isReady = platform.configured && !platform.connected;

  return (
    <div
      className={`relative border overflow-hidden flex flex-col ${
        isConnected ? "border-green-500/30" : isReady ? "border-primary/30" : "border-panel-border"
      } bg-panel-bg hover:border-primary/50 transition-all duration-300 group`}
    >
      <div
        className={`h-1 ${
          isConnected ? "bg-green-500" : isReady ? "bg-primary" : meta.accent
        } ${!isConnected && !isReady ? "opacity-30" : ""}`}
      />

      <div className="p-5 flex flex-col flex-1">
        <div className="flex items-center justify-between mb-5">
          <div className={`p-2.5 border ${meta.iconBg}`}>
            <Icon size={20} strokeWidth={1.5} />
          </div>
          <StatusBadge platform={platform} />
        </div>

        <h2 className="text-sm font-heading font-bold text-text-main mb-1.5">{platform.name}</h2>
        <p className="text-[11px] text-app-muted leading-relaxed mb-5 flex-1">{meta.description}</p>

        {!platform.configured && (
          <div className="flex items-center gap-2 p-2.5 mb-4 border border-yellow-500/20 bg-yellow-500/5 text-yellow-600 dark:text-yellow-400 text-[10px]">
            <AlertCircle size={12} className="shrink-0" />
            <span>Not configured by admin</span>
          </div>
        )}

        <ActionButton platform={platform} onConnect={onConnect} onDisconnect={onDisconnect} />
      </div>
    </div>
  );
}

function StatusBadge({ platform }: { platform: Platform }) {
  if (platform.configured && platform.connected) {
    return (
      <span className="flex items-center gap-1.5 px-2.5 py-1 text-[9px] font-heading border border-green-500/30 text-green-500 bg-green-500/10">
        <span className="relative flex h-1.5 w-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-500" />
        </span>
        CONNECTED
      </span>
    );
  }

  if (platform.configured) {
    return (
      <span className="flex items-center gap-1 px-2.5 py-1 text-[9px] font-heading border border-primary/30 text-primary bg-primary/10">
        <Plug size={9} />
        READY
      </span>
    );
  }

  return (
    <span className="flex items-center gap-1 px-2.5 py-1 text-[9px] font-heading border border-yellow-500/30 text-yellow-500 bg-yellow-500/10">
      <AlertCircle size={9} />
      UNAVAILABLE
    </span>
  );
}

function ActionButton({
  platform,
  onConnect,
  onDisconnect,
}: {
  platform: Platform;
  onConnect: (id: string) => void;
  onDisconnect: (id: string) => void;
}) {
  if (platform.configured && platform.connected) {
    return (
      <button
        type="button"
        onClick={() => onDisconnect(platform.id)}
        className="w-full py-2.5 text-[10px] font-heading border border-panel-border text-app-muted hover:border-red-500/30 hover:text-red-400 hover:bg-red-500/5 transition-colors"
      >
        DISCONNECT
      </button>
    );
  }

  if (platform.configured) {
    return (
      <button
        type="button"
        onClick={() => onConnect(platform.id)}
        className="w-full py-2.5 text-[10px] font-heading bg-primary text-white hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
      >
        <ExternalLink size={11} />
        CONNECT
      </button>
    );
  }

  return (
    <button
      type="button"
      disabled
      className="w-full py-2.5 text-[10px] font-heading border border-panel-border text-app-muted/50 cursor-not-allowed"
    >
      DISABLED
    </button>
  );
}
