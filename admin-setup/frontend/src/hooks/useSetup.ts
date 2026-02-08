import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  ConfigSummaryItem,
  ExportResponse,
  InfrastructureStatus,
  SaveStepRequest,
  SetupStatus,
  ValidateResponse,
} from "../types";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

export function useCheckAuth() {
  return useQuery<SetupStatus>({
    queryKey: ["auth-check"],
    queryFn: () => fetchApi("/api/setup/status"),
    retry: false,
  });
}

export function useSetupStatus() {
  return useQuery<SetupStatus>({
    queryKey: ["setup-status"],
    queryFn: () => fetchApi("/api/setup/status"),
  });
}

export function useInfrastructure() {
  return useQuery<InfrastructureStatus>({
    queryKey: ["infrastructure"],
    queryFn: () => fetchApi("/api/setup/infrastructure"),
  });
}

export function useStepConfig(stepId: string) {
  return useQuery<Record<string, string>>({
    queryKey: ["step-config", stepId],
    queryFn: () => fetchApi(`/api/setup/steps/${stepId}/config`),
    enabled: stepId !== "welcome" && stepId !== "review",
  });
}

export function useSaveStep() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, { stepId: string; data: SaveStepRequest }>({
    mutationFn: ({ stepId, data }) =>
      fetchApi(`/api/setup/steps/${stepId}`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["setup-status"] });
    },
  });
}

export function useValidateService() {
  return useMutation<ValidateResponse, Error, { service: string; configs: Record<string, string> }>(
    {
      mutationFn: ({ service, configs }) =>
        fetchApi(`/api/setup/validate/${service}`, {
          method: "POST",
          body: JSON.stringify({ configs }),
        }),
    },
  );
}

export function useConfigSummary() {
  return useQuery<ConfigSummaryItem[]>({
    queryKey: ["config-summary"],
    queryFn: () => fetchApi("/api/setup/summary"),
  });
}

export function useExportConfig() {
  return useQuery<ExportResponse>({
    queryKey: ["export-config"],
    queryFn: () => fetchApi("/api/setup/export"),
    enabled: false,
  });
}

export function useCompleteSetup() {
  const queryClient = useQueryClient();
  return useMutation<void, Error>({
    mutationFn: () => fetchApi("/api/setup/complete", { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["setup-status"] });
    },
  });
}

export function useResetSetup() {
  const queryClient = useQueryClient();
  return useMutation<void, Error>({
    mutationFn: () => fetchApi("/api/setup/reset", { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["setup-status"] });
      queryClient.invalidateQueries({ queryKey: ["step-config"] });
      queryClient.invalidateQueries({ queryKey: ["export-config"] });
    },
  });
}

export function useAuth() {
  return useMutation<{ authenticated: boolean }, Error, string>({
    mutationFn: (token) =>
      fetchApi("/api/auth", {
        method: "POST",
        body: JSON.stringify({ token }),
      }),
  });
}
