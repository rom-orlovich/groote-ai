import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const authToken = () => `Bearer ${localStorage.getItem("auth_token")}`;

export function useAgentScalingConfig() {
  return useQuery({
    queryKey: ["agentScaling"],
    queryFn: async () => {
      const response = await fetch("/api/user-settings/agent-scaling", {
        headers: { Authorization: authToken() },
      });
      if (!response.ok) throw new Error("Failed to fetch scaling");
      return response.json();
    },
  });
}

export function useSaveAgentScaling() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (agentCount: number) => {
      const response = await fetch("/api/user-settings/agent-scaling", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: authToken(),
        },
        body: JSON.stringify({
          agent_count: agentCount,
        }),
      });
      if (!response.ok) throw new Error("Failed to apply scaling");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agentScaling"] });
    },
  });
}
