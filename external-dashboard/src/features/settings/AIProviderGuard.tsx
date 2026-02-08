import { type ReactNode, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAIProviderStatus } from "./hooks/useAIProviderStatus";

interface AIProviderGuardProps {
  children: ReactNode;
}

export function AIProviderGuard({ children }: AIProviderGuardProps) {
  const navigate = useNavigate();
  const { data: status, isLoading, error } = useAIProviderStatus();

  useEffect(() => {
    if (!isLoading && status && !status.isConfigured) {
      navigate("/settings/ai-provider", { replace: true });
    }
  }, [status, isLoading, navigate]);

  if (isLoading) {
    return <div className="p-8 text-center font-heading">VERIFYING_CONFIGURATION...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-500 font-heading">ERROR: {(error as Error).message}</div>;
  }

  if (!status?.isConfigured) {
    return null;
  }

  return <>{children}</>;
}
