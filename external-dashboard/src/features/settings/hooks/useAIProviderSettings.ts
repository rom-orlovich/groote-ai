import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

interface SaveProviderPayload {
  provider: string;
}

const authToken = () => `Bearer ${localStorage.getItem("auth_token")}`;

export function useAIProviderSettings() {
  return useQuery({
    queryKey: ["aiProviderSettings"],
    queryFn: async () => {
      const response = await fetch("/api/user-settings/ai-provider", {
        headers: { Authorization: authToken() },
      });
      if (!response.ok) throw new Error("Failed to fetch settings");
      return response.json();
    },
  });
}

export function useSaveAIProvider() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: SaveProviderPayload) => {
      const response = await fetch("/api/user-settings/ai-provider", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: authToken(),
        },
        body: JSON.stringify({ provider: payload.provider }),
      });
      if (!response.ok) throw new Error("Failed to save settings");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["aiProviderSettings"] });
    },
  });
}
