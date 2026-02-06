import type { SetupStatus } from "../types";

export const mockSetupIncomplete: SetupStatus = {
  is_complete: false,
  current_step: "ai_provider",
  completed_steps: ["welcome"],
  skipped_steps: [],
  progress_percent: 14.3,
  total_steps: 7,
  steps: [
    "welcome",
    "ai_provider",
    "github_oauth",
    "jira_oauth",
    "slack_oauth",
    "sentry",
    "review",
  ],
  deployment_mode: "local",
  is_cloud: false,
};

export const mockSetupComplete: SetupStatus = {
  is_complete: true,
  current_step: "complete",
  completed_steps: [
    "welcome",
    "ai_provider",
    "github_oauth",
    "jira_oauth",
    "slack_oauth",
    "sentry",
  ],
  skipped_steps: [],
  progress_percent: 100.0,
  total_steps: 7,
  steps: [
    "welcome",
    "ai_provider",
    "github_oauth",
    "jira_oauth",
    "slack_oauth",
    "sentry",
    "review",
  ],
  deployment_mode: "local",
  is_cloud: false,
};

export const mockSetupPartial: SetupStatus = {
  is_complete: false,
  current_step: "github_oauth",
  completed_steps: ["welcome", "ai_provider"],
  skipped_steps: ["github_oauth"],
  progress_percent: 42.9,
  total_steps: 7,
  steps: [
    "welcome",
    "ai_provider",
    "github_oauth",
    "jira_oauth",
    "slack_oauth",
    "sentry",
    "review",
  ],
  deployment_mode: "local",
  is_cloud: false,
};
