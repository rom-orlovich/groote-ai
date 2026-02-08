import { useQueryClient } from "@tanstack/react-query";
import { AlertCircle, CheckCircle, Loader } from "lucide-react";
import { useEffect, useState } from "react";
import {
  useAIProviderSettings,
  useSaveAIProvider,
  useTestAIProvider,
} from "./hooks/useAIProviderSettings";
import { SetupInstructions } from "./SetupInstructions";

interface Settings {
  provider: string;
  api_key: string;
  model_complex: string;
  model_execution: string;
}

export function AIProviderSettings() {
  const [settings, setSettings] = useState<Settings>({
    provider: "claude",
    api_key: "",
    model_complex: "",
    model_execution: "",
  });
  const [message, setMessage] = useState<{
    type: "success" | "error" | "info";
    text: string;
  } | null>(null);
  const [isSetupComplete, setIsSetupComplete] = useState(false);

  const queryClient = useQueryClient();
  const { isLoading } = useAIProviderSettings();
  const saveMutation = useSaveAIProvider();
  const testMutation = useTestAIProvider();

  useEffect(() => {
    if (saveMutation.isSuccess) {
      setMessage({
        type: "success",
        text: "Settings saved successfully!",
      });
      setIsSetupComplete(true);
      queryClient.invalidateQueries({ queryKey: ["aiProviderStatus"] });
    }
  }, [saveMutation.isSuccess, queryClient]);

  useEffect(() => {
    if (saveMutation.isError) {
      setMessage({ type: "error", text: "Failed to save settings" });
    }
  }, [saveMutation.isError]);

  useEffect(() => {
    if (testMutation.isSuccess && testMutation.data) {
      if (testMutation.data.valid) {
        setMessage({
          type: "success",
          text: testMutation.data.message || "Connection successful",
        });
      } else {
        setMessage({ type: "error", text: testMutation.data.message });
      }
    }
  }, [testMutation.isSuccess, testMutation.data]);

  useEffect(() => {
    if (testMutation.isError) {
      setMessage({ type: "error", text: "Failed to test connection" });
    }
  }, [testMutation.isError]);

  const handleSave = () => {
    saveMutation.mutate(settings);
  };

  const handleTest = () => {
    testMutation.mutate(settings);
  };

  if (isSetupComplete) {
    return <SetupInstructions provider={settings.provider} apiKey={settings.api_key} />;
  }

  return (
    <div className="w-full space-y-6 animate-in fade-in duration-500">
      {message && <MessageBanner message={message} />}

      <div className="text-center mb-8">
        <h1 className="text-2xl font-heading font-black tracking-tighter mb-2">
          AI_PROVIDER_SETUP
        </h1>
        <p className="text-[10px] text-app-muted">
          Configure your AI provider and API credentials for task execution.
        </p>
      </div>

      <section className="panel" data-label="AI_PROVIDER">
        <div className="space-y-6">
          <FieldGroup label="PROVIDER" htmlFor="provider">
            <select
              id="provider"
              value={settings.provider}
              onChange={(e) => setSettings({ ...settings, provider: e.target.value })}
              className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm focus:outline-none focus:border-primary transition-colors"
            >
              <option value="claude">Claude (Anthropic)</option>
              <option value="cursor">Cursor AI</option>
            </select>
          </FieldGroup>

          {settings.provider === "claude" && (
            <>
              <FieldGroup
                label="API_KEY"
                htmlFor="apiKey"
                hint="Optional if using ~/.anthropic credentials"
              >
                <input
                  id="apiKey"
                  type="password"
                  placeholder="sk-ant-..."
                  value={settings.api_key}
                  onChange={(e) => setSettings({ ...settings, api_key: e.target.value })}
                  className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm focus:outline-none focus:border-primary transition-colors"
                />
              </FieldGroup>

              <div className="grid grid-cols-2 gap-4">
                <FieldGroup label="COMPLEX_MODEL" htmlFor="modelComplex" hint="For planning tasks">
                  <select
                    id="modelComplex"
                    value={settings.model_complex}
                    onChange={(e) => setSettings({ ...settings, model_complex: e.target.value })}
                    className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm focus:outline-none focus:border-primary transition-colors"
                  >
                    <option value="">Default</option>
                    <option value="opus">Opus</option>
                    <option value="sonnet">Sonnet</option>
                    <option value="haiku">Haiku</option>
                  </select>
                </FieldGroup>

                <FieldGroup
                  label="EXECUTION_MODEL"
                  htmlFor="modelExecution"
                  hint="For code execution"
                >
                  <select
                    id="modelExecution"
                    value={settings.model_execution}
                    onChange={(e) => setSettings({ ...settings, model_execution: e.target.value })}
                    className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm focus:outline-none focus:border-primary transition-colors"
                  >
                    <option value="">Default</option>
                    <option value="sonnet">Sonnet</option>
                    <option value="haiku">Haiku</option>
                  </select>
                </FieldGroup>
              </div>
            </>
          )}

          {settings.provider === "cursor" && (
            <FieldGroup label="CURSOR_API_KEY" htmlFor="cursorApiKey">
              <input
                id="cursorApiKey"
                type="password"
                placeholder="cur_..."
                value={settings.api_key}
                onChange={(e) => setSettings({ ...settings, api_key: e.target.value })}
                className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm focus:outline-none focus:border-primary transition-colors"
              />
            </FieldGroup>
          )}

          <div className="flex gap-3 pt-4 border-t border-panel-border">
            <button
              type="button"
              onClick={handleTest}
              disabled={testMutation.isPending || !settings.api_key}
              className="px-4 py-2 text-[10px] font-heading border border-panel-border text-text-main hover:border-primary transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {testMutation.isPending && <Loader size={12} className="animate-spin" />}
              TEST_CONNECTION
            </button>

            <button
              type="button"
              onClick={handleSave}
              disabled={saveMutation.isPending || isLoading}
              className="btn-primary text-[10px] font-heading disabled:opacity-50 flex items-center gap-2 ml-auto"
            >
              {saveMutation.isPending && <Loader size={12} className="animate-spin" />}
              SAVE_SETTINGS
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

function FieldGroup({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label htmlFor={htmlFor} className="block text-[10px] font-heading text-app-muted mb-2">
        {label}
      </label>
      {children}
      {hint && <p className="text-[10px] text-app-muted mt-1">{hint}</p>}
    </div>
  );
}

function MessageBanner({
  message,
}: {
  message: { type: "success" | "error" | "info"; text: string };
}) {
  const styles =
    message.type === "success"
      ? "border-green-200 dark:border-green-800 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/30"
      : message.type === "error"
        ? "border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30"
        : "border-primary text-primary bg-primary/5";

  return (
    <div className={`flex items-center gap-3 p-4 border text-[10px] font-heading ${styles}`}>
      {message.type === "success" ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
      <span>{message.text}</span>
    </div>
  );
}
