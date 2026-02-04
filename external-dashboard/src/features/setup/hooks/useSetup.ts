import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  InfrastructureStatus,
  SaveStepRequest,
  SaveStepResponse,
  SetupStatus,
  ValidateResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

async function fetchSetupStatus(): Promise<SetupStatus> {
  const res = await fetch(`${API_BASE}/api/setup/status`);
  if (!res.ok) throw new Error("Failed to fetch setup status");
  return res.json();
}

async function fetchInfrastructure(): Promise<InfrastructureStatus> {
  const res = await fetch(`${API_BASE}/api/setup/infrastructure`);
  if (!res.ok) throw new Error("Failed to check infrastructure");
  return res.json();
}

async function saveStep(step: string, data: SaveStepRequest): Promise<SaveStepResponse> {
  const res = await fetch(`${API_BASE}/api/setup/steps/${step}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to save step");
  return res.json();
}

async function validateService(
  service: string,
  credentials: Record<string, string>,
): Promise<ValidateResponse> {
  const res = await fetch(`${API_BASE}/api/setup/validate/${service}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ credentials }),
  });
  if (!res.ok) throw new Error("Failed to validate service");
  return res.json();
}

async function completeSetup(): Promise<SetupStatus> {
  const res = await fetch(`${API_BASE}/api/setup/complete`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to complete setup");
  return res.json();
}

async function resetSetup(): Promise<SetupStatus> {
  const res = await fetch(`${API_BASE}/api/setup/reset`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to reset setup");
  return res.json();
}

async function exportConfig(format = "env"): Promise<string> {
  const res = await fetch(`${API_BASE}/api/setup/export?format=${format}`);
  if (!res.ok) throw new Error("Failed to export config");
  return res.text();
}

export function useSetupStatus() {
  return useQuery({
    queryKey: ["setup-status"],
    queryFn: fetchSetupStatus,
    refetchOnWindowFocus: false,
  });
}

export function useInfrastructure() {
  return useQuery({
    queryKey: ["setup-infrastructure"],
    queryFn: fetchInfrastructure,
    enabled: false,
  });
}

export function useSaveStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ step, data }: { step: string; data: SaveStepRequest }) => saveStep(step, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["setup-status"] });
    },
  });
}

export function useValidateService() {
  return useMutation({
    mutationFn: ({
      service,
      credentials,
    }: {
      service: string;
      credentials: Record<string, string>;
    }) => validateService(service, credentials),
  });
}

export function useCompleteSetup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: completeSetup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["setup-status"] });
    },
  });
}

export function useResetSetup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: resetSetup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["setup-status"] });
    },
  });
}

export function useExportConfig() {
  return useMutation({ mutationFn: (format: string) => exportConfig(format) });
}
