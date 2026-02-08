import type { StepDefinition } from "./types";

export const STEPS: StepDefinition[] = [
  {
    id: "welcome",
    title: "INFRASTRUCTURE",
    description: "Verify database and cache connectivity before proceeding",
    category: "infrastructure",
    fields: [],
    instructions: [],
    skippable: false,
  },
  {
    id: "public_url",
    title: "PUBLIC URL",
    description: "Configure the public URL for webhooks and OAuth callbacks",
    category: "domain",
    fields: [
      {
        key: "PUBLIC_URL",
        label: "Public URL",
        placeholder: "https://your-domain.example.com",
        is_sensitive: false,
        required: true,
        helpText: "Full URL including https:// — no trailing slash",
      },
    ],
    instructions: [
      {
        text: "Choose a tunnel provider: ngrok, zrok, or your production domain",
      },
      {
        text: "All services are proxied through nginx on port 3005. Run 'make tunnel' (ngrok) or 'make tunnel-zrok' (zrok)",
      },
      {
        text: "Paste the full URL below (e.g. https://my-app.example.com). No trailing slash",
      },
    ],
    skippable: false,
  },
  {
    id: "github",
    title: "GITHUB APP",
    description: "Configure GitHub App for repository access and webhooks",
    category: "github",
    fields: [
      {
        key: "GITHUB_APP_ID",
        label: "App ID",
        placeholder: "123456",
        is_sensitive: false,
        required: true,
        helpText: "Shown at the top of your GitHub App settings page",
      },
      {
        key: "GITHUB_APP_NAME",
        label: "App Name",
        placeholder: "my-groote-ai",
        is_sensitive: false,
        required: true,
        helpText: "Must match the name used when creating the GitHub App",
      },
      {
        key: "GITHUB_CLIENT_ID",
        label: "Client ID",
        placeholder: "Iv1.abc123",
        is_sensitive: false,
        required: true,
      },
      {
        key: "GITHUB_CLIENT_SECRET",
        label: "Client Secret",
        placeholder: "secret...",
        is_sensitive: true,
        required: true,
      },
      {
        key: "GITHUB_PRIVATE_KEY_FILE",
        label: "Private Key File Path",
        placeholder: "./secrets/github-private-key.pem",
        is_sensitive: false,
        required: true,
        helpText: "Local path to the downloaded .pem file",
      },
      {
        key: "GITHUB_WEBHOOK_SECRET",
        label: "Webhook Secret",
        placeholder: "webhook-secret",
        is_sensitive: true,
        required: true,
        helpText: "The secret you set when configuring the webhook",
      },
    ],
    instructions: [
      {
        text: "Create a New GitHub App",
        url: "https://github.com/settings/apps/new",
      },
      {
        text: "Set App name (e.g. groote-ai), Homepage URL: your PUBLIC_URL, Callback URL: {PUBLIC_URL}/oauth/callback/github",
      },
      {
        text: "Enable Webhook, set a Webhook Secret, subscribe to events: Issues, Pull requests, Push, Issue comments",
      },
      {
        text: "Set permissions: Contents (R/W), Issues (R/W), Pull Requests (R/W), Metadata (Read-only)",
      },
      {
        text: "Click Create GitHub App, then generate a Private Key (.pem file downloads)",
      },
      {
        text: "Save the .pem file to ./secrets/github-private-key.pem and enter the path below",
      },
      {
        text: "Copy App ID (top of page), Client ID, and generate a Client Secret",
      },
      {
        text: "Install the App on your organization and select repositories",
      },
    ],
    skippable: true,
  },
  {
    id: "jira",
    title: "JIRA / ATLASSIAN",
    description: "Configure Jira OAuth for ticket management",
    category: "jira",
    fields: [
      {
        key: "JIRA_CLIENT_ID",
        label: "Client ID",
        placeholder: "client-id",
        is_sensitive: false,
        required: true,
      },
      {
        key: "JIRA_CLIENT_SECRET",
        label: "Client Secret",
        placeholder: "secret...",
        is_sensitive: true,
        required: true,
      },
      {
        key: "JIRA_SITE_URL",
        label: "Jira Site URL",
        placeholder: "https://your-org.atlassian.net",
        is_sensitive: false,
        required: true,
        helpText: "Your Atlassian Cloud domain (e.g. company.atlassian.net)",
      },
    ],
    instructions: [
      {
        text: "Go to Atlassian Developer Console",
        url: "https://developer.atlassian.com/console/myapps/",
      },
      {
        text: "Click Create > OAuth 2.0 integration, enter a name (e.g. groote-atlassian)",
      },
      {
        text: "Go to Authorization, configure OAuth 2.0 (3LO). Set Callback URL: {PUBLIC_URL}/oauth/callback/jira",
      },
      {
        text: "Go to Permissions > Jira API, enable: read:jira-work, write:jira-work, read:jira-user, manage:jira-webhook",
      },
      {
        text: "Go to Settings, copy Client ID and Client Secret (generate if needed)",
      },
    ],
    skippable: true,
  },
  {
    id: "slack",
    title: "SLACK APP",
    description: "Configure Slack App for notifications and commands",
    category: "slack",
    fields: [
      {
        key: "SLACK_CLIENT_ID",
        label: "Client ID",
        placeholder: "client-id",
        is_sensitive: false,
        required: true,
      },
      {
        key: "SLACK_CLIENT_SECRET",
        label: "Client Secret",
        placeholder: "secret...",
        is_sensitive: true,
        required: true,
      },
      {
        key: "SLACK_SIGNING_SECRET",
        label: "Signing Secret",
        placeholder: "signing-secret",
        is_sensitive: true,
        required: true,
        helpText: "Found under Basic Information > App Credentials",
      },
      {
        key: "SLACK_STATE_SECRET",
        label: "State Secret",
        placeholder: "random-state-secret",
        is_sensitive: true,
        required: true,
        helpText: "Random string for OAuth state validation — generate one",
      },
    ],
    instructions: [
      {
        text: "Go to Slack API Apps, click Create New App > From scratch",
        url: "https://api.slack.com/apps",
      },
      {
        text: "Enter app name (e.g. Groote AI), select your workspace",
      },
      {
        text: "Go to OAuth & Permissions, add redirect URL: {PUBLIC_URL}/oauth/callback/slack",
      },
      {
        text: "Add Bot Token Scopes: chat:write, commands, app_mentions:read, channels:read, groups:read",
      },
      {
        text: "Go to Event Subscriptions, enable events, set Request URL: {PUBLIC_URL}/webhooks/slack",
      },
      {
        text: "Subscribe to bot events: app_mention, message.channels",
      },
      {
        text: "Go to Basic Information, copy Client ID, Client Secret, and Signing Secret",
      },
    ],
    skippable: true,
  },
  {
    id: "review",
    title: "REVIEW & EXPORT",
    description: "Review all configuration and download .env file",
    category: "review",
    fields: [],
    instructions: [],
    skippable: false,
  },
];
