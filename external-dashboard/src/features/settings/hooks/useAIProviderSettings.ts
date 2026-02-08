import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

interface Settings {
  provider: string;
  api_key?: string;
  model_complex?: string;
  model_execution?: string;
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
    mutationFn: async (settings: Settings) => {
      const response = await fetch("/api/user-settings/ai-provider", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: authToken(),
        },
        body: JSON.stringify({
          provider: settings.provider,
          api_key: settings.api_key || undefined,
          model_complex: settings.model_complex || undefined,
          model_execution: settings.model_execution || undefined,
        }),
      });
      if (!response.ok) throw new Error("Failed to save settings");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["aiProviderSettings"] });
    },
  });
}

export function useTestAIProvider() {
  return useMutation({
    mutationFn: async (settings: Settings) => {
      const response = await fetch("/api/user-settings/ai-provider/test", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: authToken(),
        },
        body: JSON.stringify({
          provider: settings.provider,
          api_key: settings.api_key,
        }),
      });
      if (!response.ok) throw new Error("Failed to test");
      return response.json();
    },
  });
}
