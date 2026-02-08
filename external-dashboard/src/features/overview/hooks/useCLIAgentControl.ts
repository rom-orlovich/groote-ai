import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const authToken = () => `Bearer ${localStorage.getItem("auth_token")}`;

export interface CLIStartupStep {
  step: string;
  status: string;
  detail: string;
}

export interface CLIAgentStatus {
  provider: string;
  status: "running" | "stopped";
  version: string;
  active: boolean;
  health_check: boolean;
  startup_steps: CLIStartupStep[];
  last_checked: string;
}

export function useCLIAgentStatus() {
  return useQuery({
    queryKey: ["cli-agent-status"],
    queryFn: async () => {
      const response = await fetch("/api/cli-status", {
        headers: { Authorization: authToken() },
      });
      if (!response.ok) throw new Error("Failed to fetch CLI status");
      return response.json() as Promise<CLIAgentStatus>;
    },
    refetchInterval: 5000,
  });
}

export function useStartCLIAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await fetch("/api/cli-control/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: authToken(),
        },
      });
      if (!response.ok) throw new Error("Failed to start CLI agent");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cli-agent-status"] });
      queryClient.invalidateQueries({ queryKey: ["cli-status"] });
    },
  });
}

export function useStopCLIAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await fetch("/api/cli-control/stop", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: authToken(),
        },
      });
      if (!response.ok) throw new Error("Failed to stop CLI agent");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cli-agent-status"] });
      queryClient.invalidateQueries({ queryKey: ["cli-status"] });
    },
  });
}
