import { Check, Copy } from "lucide-react";
import { useState } from "react";

interface SetupInstructionsProps {
  provider: string;
  apiKey: string;
}

export function SetupInstructions({ provider, apiKey }: SetupInstructionsProps) {
  const [copied, setCopied] = useState(false);

  const envKey = provider === "claude" ? "ANTHROPIC_API_KEY" : "CURSOR_API_KEY";
  const envLine = `${envKey}=${apiKey}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(envLine);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-500">
      <div className="text-center">
        <h1 className="text-2xl font-heading font-black tracking-tighter mb-2">
          CONFIGURATION_SAVED
        </h1>
        <p className="text-[10px] text-app-muted">Follow the steps below to complete setup</p>
      </div>

      <section className="panel space-y-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 border border-primary flex items-center justify-center">
            <span className="text-xs font-bold">1</span>
          </div>
          <div className="flex-1">
            <h2 className="text-sm font-heading font-bold mb-3">UPDATE_YOUR_.ENV_FILE</h2>
            <p className="text-[10px] text-app-muted mb-4">
              Add the following line to your .env file in the app root directory:
            </p>
            <div className="bg-gray-950 border border-gray-700 rounded p-3 font-mono text-[9px] text-gray-300 flex items-center justify-between group hover:bg-gray-900 transition-colors">
              <span>{envLine}</span>
              <button
                type="button"
                onClick={handleCopy}
                className="ml-2 p-1 hover:bg-gray-800 rounded text-gray-500 hover:text-gray-300 transition-colors"
                title="Copy to clipboard"
              >
                {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
              </button>
            </div>
          </div>
        </div>

        <div className="h-px bg-gray-700" />

        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 border border-primary flex items-center justify-center">
            <span className="text-xs font-bold">2</span>
          </div>
          <div className="flex-1">
            <h2 className="text-sm font-heading font-bold mb-3">START_DOCKER_SERVICES</h2>
            <p className="text-[10px] text-app-muted mb-4">
              Run the following command to start all services:
            </p>
            <div className="bg-gray-950 border border-gray-700 rounded p-3 font-mono text-[9px] text-gray-300">
              make up
            </div>
            <p className="text-[10px] text-app-muted mt-3">
              Or if you prefer to use docker-compose directly:
            </p>
            <div className="bg-gray-950 border border-gray-700 rounded p-3 font-mono text-[9px] text-gray-300 mt-2">
              docker-compose up -d
            </div>
          </div>
        </div>

        <div className="h-px bg-gray-700" />

        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 border border-primary flex items-center justify-center">
            <span className="text-xs font-bold">3</span>
          </div>
          <div className="flex-1">
            <h2 className="text-sm font-heading font-bold mb-3">VERIFY_SERVICES</h2>
            <p className="text-[10px] text-app-muted mb-4">Check that all services are running:</p>
            <div className="bg-gray-950 border border-gray-700 rounded p-3 font-mono text-[9px] text-gray-300">
              make health
            </div>
            <p className="text-[10px] text-app-muted mt-3">
              Once all services show ✅, refresh this page in your browser.
            </p>
          </div>
        </div>
      </section>

      <div className="text-center">
        <p className="text-[10px] text-app-muted mb-4">
          Refresh this page once services are running
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="btn-primary text-[10px] font-heading"
        >
          REFRESH_PAGE
        </button>
      </div>
    </div>
  );
}
