import { AlertCircle, CheckCircle, ExternalLink, Plug } from "lucide-react";
import { useDisconnectPlatform, usePlatforms, type Platform } from "./hooks/usePlatforms";

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
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading platforms...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold mb-2">Connect Services</h1>
        <p className="text-gray-600">
          Connect your development tools to enable Groote AI to access your repositories, issues,
          and communications.
        </p>
      </div>

      <div className="grid gap-6">
        {platforms.map((platform: Platform) => (
          <div
            key={platform.id}
            className="border rounded-lg p-6 bg-white hover:shadow-md transition"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-xl font-semibold">{platform.name}</h2>
                  {platform.configured ? (
                    platform.connected ? (
                      <span className="flex items-center gap-1 text-green-600 bg-green-50 px-3 py-1 rounded-full text-sm">
                        <CheckCircle size={16} />
                        Connected
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-blue-600 bg-blue-50 px-3 py-1 rounded-full text-sm">
                        <Plug size={16} />
                        Ready to Connect
                      </span>
                    )
                  ) : (
                    <span className="flex items-center gap-1 text-amber-600 bg-amber-50 px-3 py-1 rounded-full text-sm">
                      <AlertCircle size={16} />
                      Not Configured
                    </span>
                  )}
                </div>

                <p className="text-gray-600 text-sm mb-4">
                  {platform.configured
                    ? platform.connected
                      ? `You're connected to ${platform.name}. You can now disconnect or keep using it.`
                      : `${platform.name} is configured by your admin. Click 'Connect' to authorize.`
                    : `Your administrator hasn't configured ${platform.name} yet. Contact them to set it up.`}
                </p>

                {!platform.configured && (
                  <p className="text-amber-700 bg-amber-50 p-3 rounded text-sm flex items-start gap-2">
                    <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
                    <span>
                      This platform is not configured by your administrator. Please contact them to
                      enable it.
                    </span>
                  </p>
                )}
              </div>

              <div className="flex gap-2 ml-4">
                {platform.configured ? (
                  platform.connected ? (
                    <button
                      type="button"
                      onClick={() => handleDisconnect(platform.id)}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition text-sm font-medium"
                    >
                      Disconnect
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleConnect(platform.id)}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm font-medium flex items-center gap-2"
                    >
                      <ExternalLink size={16} />
                      Connect
                    </button>
                  )
                ) : (
                  <button
                    type="button"
                    disabled
                    className="px-4 py-2 bg-gray-100 text-gray-400 rounded text-sm font-medium cursor-not-allowed"
                  >
                    Disabled
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Why connect these services?</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• GitHub: Access repositories, issues, and pull requests</li>
          <li>• Jira: Create and manage tickets with AI-Fix labels</li>
          <li>• Slack: Get notifications and respond to inquiries</li>
        </ul>
      </div>
    </div>
  );
}
