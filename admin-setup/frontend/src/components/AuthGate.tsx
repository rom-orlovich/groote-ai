import { Loader2 } from "lucide-react";
import { type FormEvent, type ReactNode, useState } from "react";
import { useAuth, useCheckAuth } from "../hooks/useSetup";

export function AuthGate({ children }: { children: ReactNode }) {
  const [token, setToken] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const authMutation = useAuth();
  const { isSuccess, isLoading } = useCheckAuth();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    authMutation.mutate(token, {
      onSuccess: () => setAuthenticated(true),
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-primary" />
      </div>
    );
  }

  if (authenticated || isSuccess) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="panel w-full max-w-md" data-label="AUTHENTICATION">
        <h1 className="text-sm font-heading mb-4">ADMIN_ACCESS</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="admin-token"
              className="block text-[10px] font-heading text-gray-400 mb-1"
            >
              ADMIN_SETUP_TOKEN
            </label>
            <input
              id="admin-token"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Enter admin token..."
              className="w-full bg-input-bg border border-input-border text-input-text px-3 py-2 text-sm font-mono focus:border-primary focus:outline-none"
            />
          </div>
          {authMutation.isError && (
            <p className="text-red-400 text-[10px] font-heading">INVALID_TOKEN</p>
          )}
          <button
            type="submit"
            disabled={authMutation.isPending || !token}
            className="btn-primary w-full text-[10px] disabled:opacity-50"
          >
            {authMutation.isPending ? "AUTHENTICATING..." : "AUTHENTICATE"}
          </button>
        </form>
      </div>
    </div>
  );
}
