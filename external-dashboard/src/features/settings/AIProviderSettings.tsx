import { AlertCircle, CheckCircle, Loader } from "lucide-react";
import { useEffect, useState } from "react";
import {
  useAIProviderSettings,
  useSaveAIProvider,
  useTestAIProvider,
} from "./hooks/useAIProviderSettings";

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

  const { isLoading } = useAIProviderSettings();
  const saveMutation = useSaveAIProvider();
  const testMutation = useTestAIProvider();

  useEffect(() => {
    if (saveMutation.isSuccess) {
      setMessage({ type: "success", text: "Settings saved successfully" });
      setTimeout(() => setMessage(null), 3000);
    }
  }, [saveMutation.isSuccess]);

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

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">AI Provider Settings</h1>
        <p className="text-gray-600">
          Configure your AI provider and API credentials for task execution.
        </p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-lg flex items-start gap-3 ${
            message.type === "success"
              ? "bg-green-50 text-green-800 border border-green-200"
              : message.type === "error"
                ? "bg-red-50 text-red-800 border border-red-200"
                : "bg-blue-50 text-blue-800 border border-blue-200"
          }`}
        >
          {message.type === "success" ? (
            <CheckCircle size={20} className="flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <div className="bg-white border rounded-lg p-6 space-y-6">
        <div>
          <label htmlFor="provider" className="block text-sm font-medium text-gray-700 mb-2">
            AI Provider
          </label>
          <select
            id="provider"
            value={settings.provider}
            onChange={(e) => setSettings({ ...settings, provider: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="claude">Claude (Anthropic)</option>
            <option value="cursor">Cursor AI</option>
          </select>
        </div>

        {settings.provider === "claude" && (
          <>
            <div>
              <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mb-2">
                Anthropic API Key
              </label>
              <input
                id="apiKey"
                type="password"
                placeholder="sk-ant-..."
                value={settings.api_key}
                onChange={(e) => setSettings({ ...settings, api_key: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Optional if using ~/.anthropic credentials
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="modelComplex"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Complex Model
                </label>
                <select
                  id="modelComplex"
                  value={settings.model_complex}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      model_complex: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Default</option>
                  <option value="opus">Opus</option>
                  <option value="sonnet">Sonnet</option>
                  <option value="haiku">Haiku</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">For planning tasks</p>
              </div>

              <div>
                <label
                  htmlFor="modelExecution"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Execution Model
                </label>
                <select
                  id="modelExecution"
                  value={settings.model_execution}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      model_execution: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Default</option>
                  <option value="sonnet">Sonnet</option>
                  <option value="haiku">Haiku</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">For code execution</p>
              </div>
            </div>
          </>
        )}

        {settings.provider === "cursor" && (
          <div>
            <label htmlFor="cursorApiKey" className="block text-sm font-medium text-gray-700 mb-2">
              Cursor API Key
            </label>
            <input
              id="cursorApiKey"
              type="password"
              placeholder="cur_..."
              value={settings.api_key}
              onChange={(e) => setSettings({ ...settings, api_key: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={handleTest}
            disabled={testMutation.isPending || !settings.api_key}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition disabled:opacity-50 font-medium flex items-center gap-2"
          >
            {testMutation.isPending && <Loader size={16} className="animate-spin" />}
            Test Connection
          </button>

          <button
            type="button"
            onClick={handleSave}
            disabled={saveMutation.isPending || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition disabled:opacity-50 font-medium flex items-center gap-2 ml-auto"
          >
            {saveMutation.isPending && <Loader size={16} className="animate-spin" />}
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
