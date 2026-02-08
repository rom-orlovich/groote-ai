import type { SetupStatus } from "../types";

export const mockSetupIncomplete: SetupStatus = {
  is_complete: false,
  current_step: "welcome",
  completed_steps: [],
  skipped_steps: [],
  progress_percent: 12.5,
  total_steps: 8,
  steps: [
    "welcome",
    "public_url",
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
    "public_url",
    "ai_provider",
    "github_oauth",
    "jira_oauth",
    "slack_oauth",
    "sentry",
  ],
  skipped_steps: [],
  progress_percent: 100.0,
  total_steps: 8,
  steps: [
    "welcome",
    "public_url",
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
  completed_steps: ["welcome"],
  skipped_steps: ["public_url"],
  progress_percent: 37.5,
  total_steps: 8,
  steps: [
    "welcome",
    "public_url",
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
