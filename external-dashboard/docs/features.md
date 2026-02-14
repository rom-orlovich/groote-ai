# External Dashboard - Features

## Overview

React 19 frontend dashboard for monitoring and managing groote-ai operations. Provides real-time task tracking, analytics, conversation management, webhook configuration, and system settings.

## Feature Modules

### Overview (`features/overview/`)

Dashboard home page with system metrics, recent task activity, and CLI agent controls.

**Components:**
- OverviewFeature - Main metrics dashboard
- CLIAgentControl - Start/stop/scale CLI agents

**Hooks:**
- useMetrics - Fetch system metrics from API
- useTaskLogs - Fetch recent task activity
- useCLIAgentControl - CLI agent management mutations

### Analytics (`features/analytics/`)

Cost tracking and performance analytics with time-series charts.

**Components:**
- AnalyticsFeature - Charts and metric breakdowns

**Hooks:**
- useAnalyticsData - Fetch cost, performance, and usage data

### Ledger (`features/ledger/`)

Complete task log with filtering, search, and detailed task views.

**Components:**
- LedgerFeature - Filterable task table

**Hooks:**
- useLedger - Fetch paginated task logs with filters

### Webhooks (`features/webhooks/`)

Webhook endpoint management and event history monitoring.

**Components:**
- WebhooksFeature - Webhook list and status
- CreateWebhookModal - New webhook configuration form

**Hooks:**
- useWebhooks - Fetch webhook config and event history

### Chat (`features/chat/`)

Conversation interface for interacting with AI agents. Displays message history with real-time updates.

**Components:**
- ChatFeature - Chat interface with message list and input
- TypingIndicator - Agent typing animation

**Hooks:**
- useChat - Message sending and conversation management

### Registry (`features/registry/`)

Agent registry showing available agents, their capabilities, and current status.

**Components:**
- RegistryFeature - Agent list with status indicators

**Hooks:**
- useRegistry - Fetch agent registry data

### Integrations (`features/integrations/`)

OAuth integration status for GitHub, Jira, and Slack. Shows connection status and enables OAuth flows.

**Components:**
- IntegrationsFeature - Integration cards grid
- IntegrationCard - Individual integration status

**Hooks:**
- useOAuthStatus - Fetch OAuth connection status

### Sources (`features/sources/`)

Source code repository management. Browse, add, and configure indexed repositories.

**Components:**
- SourcesFeature - Source repository list
- AddSourceModal - Add new source dialog
- SourceCard - Individual source display
- SourceConfigForm - Source configuration
- ResourcePicker - File/folder selection

**Hooks:**
- useSources - Source repository CRUD operations
- useSourceBrowser - File tree browsing

### Settings (`features/settings/`)

AI provider configuration and agent scaling settings.

**Components:**
- AIProviderSettings - API key and model configuration
- AIProviderGuard - Route guard for unconfigured providers
- AgentScalingSettings - CLI agent instance scaling
- SetupInstructions - Getting started guide

**Hooks:**
- useAIProviderSettings - Provider config mutations
- useAIProviderStatus - Check if provider is configured
- useAgentEngineStartup - Trigger Docker container startup
- useAgentScaling - Agent instance scaling mutations

### Install (`features/install/`)

Platform installation guide with step-by-step instructions for each integration.

**Components:**
- InstallPage - Multi-platform installation wizard

**Hooks:**
- usePlatforms - Platform installation status

### Setup (`features/setup/`)

Initial system setup wizard with multi-step configuration flow.

**Components:**
- SetupFeature - Multi-step setup orchestrator
- SetupGuard - Route guard for incomplete setup
- WelcomeStep - Welcome and prerequisites
- AIProviderStep - AI provider configuration
- OAuthSetupStep - OAuth app configuration
- ServiceStep - Service health checks
- ReviewStep - Configuration review
- InstructionList - Step instructions display

**Hooks:**
- useSetup - Setup state and step progression

## Shared Components

### UI Components (`components/ui/`)

| Component | Description |
|-----------|-------------|
| Header | Top navigation with sidebar toggle |
| Sidebar | Side navigation with route links |
| UsageLimits | OAuth API usage display |

### Global Hooks (`hooks/`)

| Hook | Description |
|------|-------------|
| useWebSocket | WebSocket connection lifecycle |
| useCLIStatus | CLI agent status polling |
| useTaskModal | Task detail modal state |
| useTaskStream | Real-time task event stream |
| useConversations | Conversation list and detail hooks |
| useOAuthUsage | OAuth rate limit tracking |

### Layout (`layouts/`)

| Component | Description |
|-----------|-------------|
| DashboardLayout | App shell: Header + Sidebar + Content area. Full-screen for install page, scrollable for other routes, overflow-hidden for chat. |

### Shared UI

| Component | Description |
|-----------|-------------|
| TaskStatusModal | Modal for viewing task details with tabs |
| TaskModalTabs | Tab navigation within task modal |
