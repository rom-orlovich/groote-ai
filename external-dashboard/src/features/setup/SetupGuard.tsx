import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useSetupStatus } from "./hooks/useSetup";

interface SetupGuardProps {
  children: ReactNode;
}

export function SetupGuard({ children }: SetupGuardProps) {
  const { data: status, isLoading, isError } = useSetupStatus();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background-app">
        <div className="text-center space-y-3">
          <Loader2 size={24} className="animate-spin text-orange-500 mx-auto" />
          <p className="text-[10px] font-heading text-gray-400 tracking-wider">
            CHECKING_SETUP_STATUS...
          </p>
        </div>
      </div>
    );
  }

  if (isError) {
    return <>{children}</>;
  }

  if (status && !status.is_complete) {
    return <Navigate to="/setup" replace />;
  }

  return <>{children}</>;
}
