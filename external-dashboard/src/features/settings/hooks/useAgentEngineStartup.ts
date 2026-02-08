import { useMutation } from "@tanstack/react-query";

const authToken = () => `Bearer ${localStorage.getItem("auth_token")}`;

export function useAgentEngineStartup() {
  return useMutation({
    mutationFn: async () => {
      const response = await fetch("/api/agent-engine/startup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: authToken(),
        },
      });
      if (!response.ok) throw new Error("Failed to start agent engine");
      return response.json();
    },
  });
}
