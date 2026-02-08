import type { StepDefinition } from "./types";

export const SETUP_STEPS: StepDefinition[] = [
  {
    id: "welcome",
    title: "WELCOME",
    description: "Check infrastructure and start setup",
    icon: "Rocket",
    skippable: false,
    fields: [],
  },
  {
    id: "public_url",
    title: "DOMAIN",
    description: "Set the public URL for webhooks, OAuth callbacks, and dashboard access",
    icon: "Globe",
    skippable: false,
    stepType: "service",
    instructions: [
      {
        step: 1,
        title: "Choose a Tunnel Provider",
        description:
          "You need a public URL to receive webhooks. Use any tunnel provider (zrok, ngrok, cloudflare tunnel) or your production domain",
      },
      {
        step: 2,
        title: "Get Your Public URL",
        description:
          "Run your tunnel provider to get a public URL. All services are proxied through nginx on port 3005",
      },
      {
        step: 3,
        title: "Enter the URL Below",
        description:
          "Paste the full URL (e.g. https://my-app.example.com). This will be used for webhook endpoints, OAuth callbacks, and dashboard access",
      },
    ],
    fields: [
      {
        key: "PUBLIC_URL",
        label: "Public URL",
        placeholder: "https://my-app.example.com",
        sensitive: false,
        required: true,
        helpText: "Full URL including https:// — no trailing slash",
      },
    ],
  },
  {
    id: "ai_provider",
    title: "AI_PROVIDER",
    description: "Configure your AI execution engine",
    icon: "Brain",
    skippable: false,
    stepType: "ai_provider",
    fields: [],
    providerGroups: [
      {
        provider: "claude",
        validationService: "anthropic",
        fields: [
          {
            key: "ANTHROPIC_API_KEY",
            label: "Anthropic API Key",
            placeholder: "sk-ant-...",
            sensitive: true,
            required: false,
            helpText: "Optional if using ~/.anthropic credentials",
          },
          {
            key: "CLAUDE_MODEL_COMPLEX",
            label: "Complex Model",
            placeholder: "opus",
            sensitive: false,
            required: false,
            helpText: "For planning tasks (opus/sonnet)",
          },
          {
            key: "CLAUDE_MODEL_EXECUTION",
            label: "Execution Model",
            placeholder: "sonnet",
            sensitive: false,
            required: false,
            helpText: "For code execution (sonnet/haiku)",
          },
        ],
      },
      {
        provider: "cursor",
        validationService: "cursor",
        fields: [
          {
            key: "CURSOR_API_KEY",
            label: "Cursor API Key",
            placeholder: "cur_...",
            sensitive: true,
            required: false,
            helpText: "API key for Cursor AI",
          },
          {
            key: "CURSOR_MODEL_COMPLEX",
            label: "Complex Model",
            placeholder: "claude-3.5-sonnet",
            sensitive: false,
            required: false,
            helpText: "For planning tasks",
          },
          {
            key: "CURSOR_MODEL_EXECUTION",
            label: "Execution Model",
            placeholder: "claude-3.5-sonnet",
            sensitive: false,
            required: false,
            helpText: "For code execution",
          },
        ],
      },
    ],
  },
  {
    id: "github_oauth",
    title: "GITHUB",
    description: "Create a GitHub App for repository automation",
    icon: "Github",
    skippable: true,
    stepType: "oauth_setup",
    oauthPlatform: "github",
    validationService: "github_oauth",
    webhookMode: "auto",
    instructions: [
      {
        step: 1,
        title: "Create a New GitHub App",
        description: "Go to GitHub > Settings > Developer settings > GitHub Apps > New GitHub App",
        link: "https://github.com/settings/apps/new",
      },
      {
        step: 2,
        title: "Fill App Details",
        description:
          "GitHub App name: your-org-groote | Homepage URL: {origin} | Callback URL: {origin}/oauth/callback/github",
      },
      {
        step: 3,
        title: "Configure Webhook",
        description:
          "Enable Active webhook. Set a Webhook secret (save it for the field below). Subscribe to events: Issues, Pull requests, Push, Issue comments, Pull request reviews. The webhook URL will be auto-configured when users connect",
      },
      {
        step: 4,
        title: "Set Permissions",
        description:
          "Under Permissions > Repository: Contents (Read & Write), Issues (Read & Write), Pull requests (Read & Write), Metadata (Read-only). Under Permissions > Organization: Members (Read-only)",
      },
      {
        step: 5,
        title: "Create App & Generate Private Key",
        description:
          "Click Create GitHub App. Then on the app page, scroll to Private keys and click Generate a private key. A .pem file will download - paste its contents below",
      },
      {
        step: 6,
        title: "Copy Credentials",
        description:
          "From the app settings page, copy: App ID (top of page), Client ID, and generate a Client Secret",
      },
      {
        step: 7,
        title: "Install the App",
        description:
          "Go to Install App in the sidebar and install it on your organization or account. Select the repositories you want Groote to access",
      },
    ],
    fields: [
      {
        key: "GITHUB_APP_ID",
        label: "App ID",
        placeholder: "123456",
        sensitive: false,
        required: true,
        helpText: "Shown on the GitHub App settings page",
      },
      {
        key: "GITHUB_CLIENT_ID",
        label: "Client ID",
        placeholder: "Iv1.abc123...",
        sensitive: false,
        required: true,
      },
      {
        key: "GITHUB_CLIENT_SECRET",
        label: "Client Secret",
        placeholder: "your-client-secret",
        sensitive: true,
        required: true,
      },
      {
        key: "GITHUB_PRIVATE_KEY",
        label: "Private Key (PEM)",
        placeholder: "-----BEGIN RSA PRIVATE KEY-----\n...",
        sensitive: true,
        required: true,
        multiline: true,
      },
      {
        key: "GITHUB_WEBHOOK_SECRET",
        label: "Webhook Secret",
        placeholder: "your-webhook-secret",
        sensitive: true,
        required: false,
        helpText: "For webhook signature validation",
      },
    ],
  },
  {
    id: "jira_oauth",
    title: "ATLASSIAN",
    description: "Create an Atlassian OAuth app for Jira and Confluence",
    icon: "ClipboardList",
    skippable: true,
    stepType: "oauth_setup",
    oauthPlatform: "jira",
    validationService: "jira_oauth",
    webhookMode: "auto",
    instructions: [
      {
        step: 1,
        title: "Create an Atlassian App",
        description:
          "Go to Atlassian Developer Console. Click Create > OAuth 2.0 integration. Enter a name (e.g. groote-atlassian) and accept the terms",
        link: "https://developer.atlassian.com/console/myapps/",
      },
      {
        step: 2,
        title: "Enable OAuth 2.0 (3LO)",
        description:
          "In the app sidebar, go to Authorization. Click Configure next to OAuth 2.0 (3LO). Set Callback URL: {origin}/oauth/callback/jira",
      },
      {
        step: 3,
        title: "Add Jira API Permissions",
        description:
          "Go to Permissions in the sidebar. Under Jira API, click Add and enable: read:jira-work, write:jira-work, read:jira-user, manage:jira-webhook",
      },
      {
        step: 4,
        title: "Add Confluence API Permissions",
        description:
          "Under Confluence API, click Add and enable: read:confluence-content.all, read:confluence-space.summary, read:confluence-props, write:confluence-content, write:confluence-file",
      },
      {
        step: 5,
        title: "Copy Credentials",
        description:
          "Go to Settings in the sidebar. Copy the Client ID and Secret. If no secret exists, click Create Secret to generate one",
      },
    ],
    fields: [
      {
        key: "JIRA_CLIENT_ID",
        label: "Client ID",
        placeholder: "your-jira-client-id",
        sensitive: false,
        required: true,
      },
      {
        key: "JIRA_CLIENT_SECRET",
        label: "Client Secret",
        placeholder: "your-jira-client-secret",
        sensitive: true,
        required: true,
      },
    ],
  },
  {
    id: "slack_oauth",
    title: "SLACK",
    description: "Create a Slack App for chat notifications",
    icon: "MessageSquare",
    skippable: true,
    stepType: "oauth_setup",
    oauthPlatform: "slack",
    validationService: "slack_oauth",
    webhookMode: "manual",
    instructions: [
      {
        step: 1,
        title: "Create a Slack App",
        description:
          "Go to Slack API and click Create New App. Choose From scratch. Enter an app name (e.g. Groote AI) and select your workspace",
        link: "https://api.slack.com/apps",
      },
      {
        step: 2,
        title: "Set OAuth Redirect URL",
        description:
          "Go to OAuth & Permissions in the sidebar. Under Redirect URLs, click Add New Redirect URL and enter: {origin}/oauth/callback/slack",
      },
      {
        step: 3,
        title: "Add Bot Token Scopes",
        description:
          "On the same OAuth & Permissions page, scroll to Scopes > Bot Token Scopes. Add: chat:write, commands, app_mentions:read, channels:read, groups:read",
      },
      {
        step: 4,
        title: "Enable Event Subscriptions",
        description:
          "Go to Event Subscriptions in the sidebar. Toggle Enable Events to On. Set Request URL: {origin}/api/webhooks/slack. Under Subscribe to bot events, add: app_mention, message.channels",
      },
      {
        step: 5,
        title: "Copy Credentials",
        description:
          "Go to Basic Information in the sidebar. Copy Client ID, Client Secret, and Signing Secret from the App Credentials section",
      },
      {
        step: 6,
        title: "Install to Workspace",
        description:
          "Go to Install App in the sidebar. Click Install to Workspace and authorize the app. The bot will appear in your workspace",
      },
    ],
    fields: [
      {
        key: "SLACK_CLIENT_ID",
        label: "Client ID",
        placeholder: "your-slack-client-id",
        sensitive: false,
        required: true,
      },
      {
        key: "SLACK_CLIENT_SECRET",
        label: "Client Secret",
        placeholder: "your-slack-client-secret",
        sensitive: true,
        required: true,
      },
      {
        key: "SLACK_SIGNING_SECRET",
        label: "Signing Secret",
        placeholder: "your-signing-secret",
        sensitive: true,
        required: false,
        helpText: "For request signature validation",
      },
    ],
  },
  {
    id: "sentry",
    title: "SENTRY",
    description: "Connect Sentry for error tracking and alerts",
    icon: "AlertTriangle",
    skippable: true,
    stepType: "service",
    validationService: "sentry",
    instructions: [
      {
        step: 1,
        title: "Create a Sentry Project",
        description:
          "Log in to Sentry. Go to Projects > Create Project. Choose your platform (e.g. Python/Node.js) and name it (e.g. groote-ai)",
        link: "https://sentry.io/organizations/",
      },
      {
        step: 2,
        title: "Get Your Auth Token",
        description:
          "Go to Settings > Auth Tokens. Click Create New Token. Select scopes: project:read, org:read, event:read. Copy the token",
        link: "https://sentry.io/settings/auth-tokens/",
      },
      {
        step: 3,
        title: "Get the DSN",
        description:
          "Go to your project Settings > Client Keys (DSN). Copy the DSN URL (looks like https://xxx@xxx.ingest.sentry.io/xxx)",
      },
      {
        step: 4,
        title: "Find Your Organization Slug",
        description:
          "Your org slug is in the Sentry URL: sentry.io/organizations/{your-org-slug}/. Copy just the slug part",
      },
    ],
    fields: [
      {
        key: "SENTRY_AUTH_TOKEN",
        label: "Auth Token",
        placeholder: "your-auth-token",
        sensitive: true,
        required: true,
        helpText: "sentry.io/settings/auth-tokens",
      },
      {
        key: "SENTRY_DSN",
        label: "DSN",
        placeholder: "https://xxx@sentry.io/xxx",
        sensitive: true,
        required: false,
        helpText: "Project DSN for error reporting",
      },
      {
        key: "SENTRY_ORG_SLUG",
        label: "Organization Slug",
        placeholder: "your-org",
        sensitive: false,
        required: false,
      },
    ],
  },
  {
    id: "review",
    title: "REVIEW",
    description: "Review configuration and complete setup",
    icon: "CheckCircle",
    skippable: false,
    fields: [],
  },
];
