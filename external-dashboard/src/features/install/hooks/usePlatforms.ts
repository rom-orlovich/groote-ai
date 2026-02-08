import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export interface Platform {
  id: string;
  name: string;
  configured: boolean;
  connected: boolean;
}

const authToken = () => `Bearer ${localStorage.getItem("auth_token")}`;

export function usePlatforms() {
  return useQuery({
    queryKey: ["platforms"],
    queryFn: async () => {
      const response = await fetch("/api/oauth/platforms");
      if (!response.ok) throw new Error("Failed to fetch platforms");
      return response.json();
    },
    initialData: {
      platforms: [
        { id: "github", name: "GitHub", configured: false, connected: false },
        { id: "jira", name: "Jira", configured: false, connected: false },
        { id: "slack", name: "Slack", configured: false, connected: false },
      ],
    },
  });
}

export function useDisconnectPlatform() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (platformId: string) => {
      const response = await fetch(`/api/oauth/disconnect/${platformId}`, {
        method: "POST",
        headers: { Authorization: authToken() },
      });
      if (!response.ok) throw new Error("Failed to disconnect");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["platforms"] });
    },
  });
}
