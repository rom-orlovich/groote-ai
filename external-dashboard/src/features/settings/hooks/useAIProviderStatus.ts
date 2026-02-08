import { useQuery } from "@tanstack/react-query";

interface AIProviderStatus {
  isConfigured: boolean;
  provider: string | null;
}

const authToken = () => `Bearer ${localStorage.getItem("auth_token")}`;

export function useAIProviderStatus() {
  return useQuery<AIProviderStatus>({
    queryKey: ["aiProviderStatus"],
    queryFn: async () => {
      const response = await fetch("/api/user-settings/ai-provider", {
        headers: { Authorization: authToken() },
      });
      if (!response.ok) throw new Error("Failed to fetch AI provider status");
      const data = await response.json();
      return {
        isConfigured: data.provider !== null && data.provider !== undefined,
        provider: data.provider,
      };
    },
    retry: 1,
  });
}
