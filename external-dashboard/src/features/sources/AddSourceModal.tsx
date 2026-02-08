import {
  AlertTriangle,
  CheckCircle,
  FileText,
  GitBranch,
  Link2,
  TicketIcon,
  X,
} from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import type { CreateSourceRequest, SourceTypeInfo } from "./hooks/useSources";
import { useSourceTypes } from "./hooks/useSources";
import { ResourcePicker } from "./ResourcePicker";
import type { ConfluenceConfig, GitHubConfig, JiraConfig } from "./SourceConfigForm";
import { SourceConfigForm } from "./SourceConfigForm";

interface AddSourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (request: CreateSourceRequest) => void;
  isSubmitting: boolean;
}

type SourceType = "github" | "jira" | "confluence";
type ModalStep = "select" | "browse" | "configure";

const SOURCE_ICONS: Record<string, typeof GitBranch> = {
  github: GitBranch,
  jira: TicketIcon,
  confluence: FileText,
};

const STEP_TITLES: Record<ModalStep, string> = {
  select: "ADD_DATA_SOURCE",
  browse: "BROWSE_RESOURCES",
  configure: "CONFIGURE_SOURCE",
};

export function AddSourceModal({ isOpen, onClose, onSubmit, isSubmitting }: AddSourceModalProps) {
  const [step, setStep] = useState<ModalStep>("select");
  const [selectedType, setSelectedType] = useState<SourceType | null>(null);
  const [selectedTypeInfo, setSelectedTypeInfo] = useState<SourceTypeInfo | null>(null);
  const [selectedResourceIds, setSelectedResourceIds] = useState<string[]>([]);
  const [name, setName] = useState("");

  const { data: sourceTypes, isLoading: isLoadingTypes } = useSourceTypes();

  const [githubConfig, setGithubConfig] = useState<GitHubConfig>({
    include_patterns: "",
    exclude_patterns: "",
    branches: "main, master",
    file_patterns: "**/*.py, **/*.ts, **/*.js, **/*.go",
  });

  const [jiraConfig, setJiraConfig] = useState<JiraConfig>({
    jql: "",
    issue_types: "Bug, Story, Task",
    include_labels: "",
    max_results: 1000,
  });

  const [confluenceConfig, setConfluenceConfig] = useState<ConfluenceConfig>({
    spaces: "",
    include_labels: "",
    content_types: "page, blogpost",
  });

  const handleTypeSelect = (typeInfo: SourceTypeInfo) => {
    setSelectedType(typeInfo.source_type as SourceType);
    setSelectedTypeInfo(typeInfo);
    setName(`${typeInfo.name} Source`);
    if (typeInfo.oauth_connected) {
      setStep("browse");
    } else {
      setStep("configure");
    }
  };

  const handleBrowseNext = () => {
    if (selectedType === "github") {
      setGithubConfig({ ...githubConfig, include_patterns: selectedResourceIds.join(", ") });
    } else if (selectedType === "jira") {
      setJiraConfig({ ...jiraConfig, jql: `project IN (${selectedResourceIds.join(", ")})` });
    } else if (selectedType === "confluence") {
      setConfluenceConfig({ ...confluenceConfig, spaces: selectedResourceIds.join(", ") });
    }
    setStep("configure");
  };

  const handleSubmit = () => {
    if (!selectedType || !name) return;

    let config: Record<string, unknown> = {};

    if (selectedType === "github") {
      config = {
        include_patterns: githubConfig.include_patterns
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        exclude_patterns: githubConfig.exclude_patterns
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        branches: githubConfig.branches
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        file_patterns: githubConfig.file_patterns
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      };
    } else if (selectedType === "jira") {
      config = {
        jql: jiraConfig.jql,
        issue_types: jiraConfig.issue_types
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        include_labels: jiraConfig.include_labels
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        max_results: jiraConfig.max_results,
      };
    } else if (selectedType === "confluence") {
      config = {
        spaces: confluenceConfig.spaces
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        include_labels: confluenceConfig.include_labels
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        content_types: confluenceConfig.content_types
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      };
    }

    onSubmit({ name, source_type: selectedType, config, enabled: true });
  };

  const handleClose = () => {
    setStep("select");
    setSelectedType(null);
    setSelectedTypeInfo(null);
    setSelectedResourceIds([]);
    setName("");
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-modal-bg border border-modal-border w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-4 border-b border-modal-border">
          <h2 className="font-heading text-sm text-text-main">{STEP_TITLES[step]}</h2>
          <button
            type="button"
            onClick={handleClose}
            className="p-1 hover:bg-panel-border/30 text-text-main"
          >
            <X size={16} />
          </button>
        </div>

        <div className="p-4">
          {step === "select" && (
            <SelectStep
              sourceTypes={sourceTypes}
              isLoadingTypes={isLoadingTypes}
              onTypeSelect={handleTypeSelect}
            />
          )}

          {step === "browse" && selectedType && (
            <ResourcePicker
              platform={selectedType}
              selectedIds={selectedResourceIds}
              onSelectionChange={setSelectedResourceIds}
              onBack={() => setStep("select")}
              onNext={handleBrowseNext}
            />
          )}

          {step === "configure" && selectedType && (
            <div className="space-y-4">
              <SourceConfigForm
                sourceType={selectedType}
                name={name}
                onNameChange={setName}
                githubConfig={githubConfig}
                onGithubConfigChange={setGithubConfig}
                jiraConfig={jiraConfig}
                onJiraConfigChange={setJiraConfig}
                confluenceConfig={confluenceConfig}
                onConfluenceConfigChange={setConfluenceConfig}
                selectedTypeInfo={selectedTypeInfo}
              />
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setStep("select")}
                  className="flex-1 px-4 py-2 border border-panel-border hover:bg-panel-border/20 text-[10px] font-heading text-text-main"
                >
                  BACK
                </button>
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={isSubmitting || !name}
                  className="flex-1 px-4 py-2 bg-cta text-white hover:opacity-90 text-[10px] font-heading disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? "CREATING..." : "CREATE_SOURCE"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SelectStep({
  sourceTypes,
  isLoadingTypes,
  onTypeSelect,
}: {
  sourceTypes: SourceTypeInfo[] | undefined;
  isLoadingTypes: boolean;
  onTypeSelect: (typeInfo: SourceTypeInfo) => void;
}) {
  return (
    <div className="grid gap-3">
      <p className="text-[10px] text-app-muted mb-2">
        Select the type of data source you want to add. Each source will be indexed and made
        searchable for the AI agent.
      </p>
      {isLoadingTypes ? (
        <div className="text-center py-4 text-[10px] text-app-muted">Loading source types...</div>
      ) : (
        sourceTypes?.map((typeInfo) => {
          const Icon = SOURCE_ICONS[typeInfo.source_type] || FileText;
          return (
            <button
              type="button"
              key={typeInfo.source_type}
              onClick={() => onTypeSelect(typeInfo)}
              className={`flex items-center gap-3 p-3 border text-left transition-colors ${
                typeInfo.oauth_connected
                  ? "border-panel-border hover:border-primary/50 hover:bg-panel-border/20"
                  : "border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-950/30"
              }`}
            >
              <div className="p-2 border border-panel-border text-text-main">
                <Icon size={20} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-heading text-sm text-text-main">{typeInfo.name}</span>
                  {typeInfo.oauth_connected ? (
                    <CheckCircle size={12} className="text-green-500" />
                  ) : (
                    <AlertTriangle size={12} className="text-amber-500" />
                  )}
                </div>
                <div className="text-[10px] text-app-muted">{typeInfo.description}</div>
                {!typeInfo.oauth_connected && (
                  <div className="text-[10px] text-amber-600 dark:text-amber-400 mt-1">
                    OAuth not connected -
                    <Link
                      to="/integrations"
                      className="inline-flex items-center gap-1 ml-1 hover:text-amber-800"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Link2 size={10} />
                      Connect
                    </Link>
                  </div>
                )}
              </div>
            </button>
          );
        })
      )}
    </div>
  );
}
