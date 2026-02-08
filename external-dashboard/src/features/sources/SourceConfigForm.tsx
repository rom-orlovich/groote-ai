import { AlertTriangle, Link2 } from "lucide-react";
import { Link } from "react-router-dom";
import type { SourceTypeInfo } from "./hooks/useSources";

export interface GitHubConfig {
  include_patterns: string;
  exclude_patterns: string;
  branches: string;
  file_patterns: string;
}

export interface JiraConfig {
  jql: string;
  issue_types: string;
  include_labels: string;
  max_results: number;
}

export interface ConfluenceConfig {
  spaces: string;
  include_labels: string;
  content_types: string;
}

interface SourceConfigFormProps {
  sourceType: "github" | "jira" | "confluence";
  name: string;
  onNameChange: (name: string) => void;
  githubConfig: GitHubConfig;
  onGithubConfigChange: (config: GitHubConfig) => void;
  jiraConfig: JiraConfig;
  onJiraConfigChange: (config: JiraConfig) => void;
  confluenceConfig: ConfluenceConfig;
  onConfluenceConfigChange: (config: ConfluenceConfig) => void;
  selectedTypeInfo?: SourceTypeInfo | null;
}

export function SourceConfigForm({
  sourceType,
  name,
  onNameChange,
  githubConfig,
  onGithubConfigChange,
  jiraConfig,
  onJiraConfigChange,
  confluenceConfig,
  onConfluenceConfigChange,
  selectedTypeInfo,
}: SourceConfigFormProps) {
  return (
    <div className="space-y-4">
      {selectedTypeInfo && !selectedTypeInfo.oauth_connected && (
        <div className="p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-[10px]">
          <div className="flex items-center gap-1 text-amber-700 dark:text-amber-400 mb-1">
            <AlertTriangle size={12} />
            <span className="font-heading">OAUTH_NOT_CONNECTED</span>
          </div>
          <p className="text-amber-600 dark:text-amber-400 mb-2">
            You can configure this source, but it will be created as disabled. Connect{" "}
            {selectedTypeInfo.oauth_platform} OAuth to enable syncing.
          </p>
          <Link
            to="/integrations"
            className="inline-flex items-center gap-1 text-amber-700 dark:text-amber-400 hover:text-amber-900 dark:hover:text-amber-300 font-heading"
          >
            <Link2 size={10} />
            GO_TO_INTEGRATIONS
          </Link>
        </div>
      )}

      <div>
        <label className="block text-[10px] font-heading text-app-muted mb-1">
          SOURCE_NAME
          <input
            type="text"
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm focus:outline-none focus:border-primary mt-1"
            placeholder="Enter source name"
          />
        </label>
      </div>

      {sourceType === "github" && (
        <GitHubFields config={githubConfig} onChange={onGithubConfigChange} />
      )}

      {sourceType === "jira" && <JiraFields config={jiraConfig} onChange={onJiraConfigChange} />}

      {sourceType === "confluence" && (
        <ConfluenceFields config={confluenceConfig} onChange={onConfluenceConfigChange} />
      )}
    </div>
  );
}

function GitHubFields({
  config,
  onChange,
}: {
  config: GitHubConfig;
  onChange: (c: GitHubConfig) => void;
}) {
  return (
    <>
      <div>
        <label className="block text-[10px] font-heading text-app-muted mb-1">
          INCLUDE_PATTERNS (comma-separated)
          <input
            type="text"
            value={config.include_patterns}
            onChange={(e) => onChange({ ...config, include_patterns: e.target.value })}
            className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm font-mono focus:outline-none focus:border-primary mt-1"
            placeholder="owner/repo, owner/repo-*"
          />
        </label>
      </div>
      <div>
        <label className="block text-[10px] font-heading text-app-muted mb-1">
          BRANCHES (comma-separated)
          <input
            type="text"
            value={config.branches}
            onChange={(e) => onChange({ ...config, branches: e.target.value })}
            className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm font-mono focus:outline-none focus:border-primary mt-1"
            placeholder="main, master, develop"
          />
        </label>
      </div>
      <div>
        <label className="block text-[10px] font-heading text-app-muted mb-1">
          FILE_PATTERNS (comma-separated)
          <input
            type="text"
            value={config.file_patterns}
            onChange={(e) => onChange({ ...config, file_patterns: e.target.value })}
            className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm font-mono focus:outline-none focus:border-primary mt-1"
            placeholder="**/*.py, **/*.ts"
          />
        </label>
      </div>
    </>
  );
}

function JiraFields({
  config,
  onChange,
}: {
  config: JiraConfig;
  onChange: (c: JiraConfig) => void;
}) {
  return (
    <>
      <div>
        <label className="block text-[10px] font-heading text-app-muted mb-1">
          JQL_FILTER (optional)
          <input
            type="text"
            value={config.jql}
            onChange={(e) => onChange({ ...config, jql: e.target.value })}
            className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm font-mono focus:outline-none focus:border-primary mt-1"
            placeholder="project = PROJ AND status != Done"
          />
        </label>
      </div>
      <div>
        <label className="block text-[10px] font-heading text-app-muted mb-1">
          ISSUE_TYPES (comma-separated)
          <input
            type="text"
            value={config.issue_types}
            onChange={(e) => onChange({ ...config, issue_types: e.target.value })}
            className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm font-mono focus:outline-none focus:border-primary mt-1"
            placeholder="Bug, Story, Task"
          />
        </label>
      </div>
      <div>
        <label className="block text-[10px] font-heading text-app-muted mb-1">
          MAX_RESULTS
          <input
            type="number"
            value={config.max_results}
            onChange={(e) =>
              onChange({ ...config, max_results: parseInt(e.target.value, 10) || 1000 })
            }
            className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm font-mono focus:outline-none focus:border-primary mt-1"
          />
        </label>
      </div>
    </>
  );
}

function ConfluenceFields({
  config,
  onChange,
}: {
  config: ConfluenceConfig;
  onChange: (c: ConfluenceConfig) => void;
}) {
  return (
    <>
      <div>
        <label className="block text-[10px] font-heading text-app-muted mb-1">
          SPACES (comma-separated, leave empty for all)
          <input
            type="text"
            value={config.spaces}
            onChange={(e) => onChange({ ...config, spaces: e.target.value })}
            className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm font-mono focus:outline-none focus:border-primary mt-1"
            placeholder="ENG, DOCS, WIKI"
          />
        </label>
      </div>
      <div>
        <label className="block text-[10px] font-heading text-app-muted mb-1">
          CONTENT_TYPES (comma-separated)
          <input
            type="text"
            value={config.content_types}
            onChange={(e) => onChange({ ...config, content_types: e.target.value })}
            className="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text text-sm font-mono focus:outline-none focus:border-primary mt-1"
            placeholder="page, blogpost"
          />
        </label>
      </div>
    </>
  );
}
