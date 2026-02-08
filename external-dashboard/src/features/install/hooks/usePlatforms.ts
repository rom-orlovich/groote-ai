import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export interface Platform {
  id: string;
  name: string;
  configured: boolean;
  connected: boolean;
}

interface OAuthStatusResponse {
  success: boolean;
  statuses: Record<
    string,
    {
      platform: string;
      name: string;
      connected: boolean;
      configured: boolean;
    }
  >;
}

const PLATFORM_ORDER = ["github", "jira", "slack"];

export function usePlatforms() {
  return useQuery({
    queryKey: ["platforms"],
    queryFn: async (): Promise<{ platforms: Platform[] }> => {
      const response = await fetch("/api/oauth/status");
      if (!response.ok) throw new Error("Failed to fetch platforms");
      const data: OAuthStatusResponse = await response.json();

      const platforms = PLATFORM_ORDER.map((key) => {
        const status = data.statuses[key];
        if (!status) return { id: key, name: key, configured: false, connected: false };
        return {
          id: status.platform,
          name: status.name,
          configured: status.configured,
          connected: status.connected,
        };
      });

      return { platforms };
    },
  });
}

export function useDisconnectPlatform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (platformId: string) => {
      const response = await fetch(`/api/oauth/revoke/${platformId}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Failed to disconnect");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["platforms"] });
    },
  });
}
