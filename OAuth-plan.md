# Groote AI — Full Session Context & OAuth Implementation Plan

## Session Summary (Completed Work)

### What Was Done

All Docker services are now running and healthy after fixing these issues:

1. **Docker build fixes**: BuildKit cache corruption, `.dockerignore` for node_modules, Rust 1.75→1.88 upgrade, port 5000/6379 conflicts
2. **api-gateway**: Created missing `middleware/__init__.py` and `error_handler.py`
3. **dashboard-api**: Created missing `core/webhook_config_loader.py`, remapped port 5000→5001 (macOS AirPlay conflict)
4. **oauth-service**: Created local `models.py` (was importing from `agent_engine.models` which doesn't exist), fixed imports in `installation_service.py` and `token_service.py`
5. **task-logger**: Fixed structlog-style kwargs → stdlib `%`-format logging
6. **sentry-api**: Made `sentry_auth_token` and `sentry_org_slug` optional with defaults
7. **chromadb**: Updated image from 0.4.22→0.5.23 (NumPy 2.0 incompatibility)
8. **knowledge-graph**: Fixed Alpine version mismatch (3.19→3.22), cargo cache dummy binary bug (`touch src/main.rs`), entrypoint `exec` with background process
9. **MCP servers**: Fixed healthchecks from curl to TCP socket checks, fixed knowledge-graph-mcp Dockerfile
10. **Setup wizard**: Changed API_BASE from `http://localhost:5000` to `""` (nginx proxy), fixed DateTime timezone columns, made Anthropic API Key optional with credential-based auth fallback

### Current State

- All services running: `make up` succeeds
- Setup wizard accessible at `http://localhost:3005/setup`
- Infrastructure checks pass (PostgreSQL, Redis)
- Setup flow works end-to-end (welcome → steps → review)
- Branch: `claude/setup-tutorial-dashboard-PqMuI`

---

## OAuth Implementation Plan (Pending — Next Session)

### Goal

Restructure the setup wizard (admin) and dashboard integrations (end-user) to use OAuth instead of static tokens.

- **Admin flow (Setup Wizard):** Interactive screens guide the admin through creating OAuth apps on each platform (GitHub App, Jira OAuth app, Slack App). Admin enters Client ID/Secret which are saved to DB.
- **End-user flow (Dashboard Integrations):** Simple "Connect" buttons trigger OAuth flows. Users never see credentials — they just authorize.

---

### Phase 1: Nginx Proxy for OAuth Service

**File:** `external-dashboard/nginx.conf`

- Add `/oauth/` location block that proxies to `oauth-service:8000`
- Enables the frontend to reach OAuth endpoints through the same origin (no CORS issues)

---

### Phase 2: OAuth Callback Redirect

**File:** `oauth-service/api/routes.py`

- Change `/callback/{platform}` endpoint to return `RedirectResponse` to the frontend instead of raw JSON
- Redirect URL: `/integrations?oauth_callback={platform}&success=true` (or `&error=...` on failure)

**File:** `dashboard-api/api/oauth_status.py`

- Update `redirect_url` in install response to use relative path (`/oauth/install/{platform}`) instead of internal Docker URL

---

### Phase 3: New Setup Step Definitions

**File:** `external-dashboard/src/features/setup/constants.ts`

- Replace `github`, `jira`, `slack`, `sentry` steps with OAuth-focused steps: `github_oauth`, `jira_oauth`, `slack_oauth`
- Remove `sentry` from wizard (Sentry uses auth tokens, not OAuth — keep as simple token step or move to advanced)
- Each step has `fields` for Client ID/Secret + `instructions` array with platform-specific guidance
- Keep `welcome`, `ai_provider`, and `review` steps unchanged

Example step structure:
```typescript
{
  id: "github_oauth",
  title: "GITHUB",
  description: "Create a GitHub App for repository automation",
  icon: "Github",
  skippable: true,
  stepType: "oauth_setup",
  oauthPlatform: "github",
  fields: [
    { key: "GITHUB_APP_ID", label: "App ID", sensitive: false, required: true },
    { key: "GITHUB_CLIENT_ID", label: "Client ID", sensitive: false, required: true },
    { key: "GITHUB_CLIENT_SECRET", label: "Client Secret", sensitive: true, required: true },
    { key: "GITHUB_PRIVATE_KEY", label: "Private Key (PEM)", sensitive: true, required: true, multiline: true },
  ],
  instructions: [
    { step: 1, title: "Go to GitHub Settings", description: "Navigate to github.com/settings/apps > New GitHub App", link: "https://github.com/settings/apps/new" },
    { step: 2, title: "Fill App Details", description: "Name: your-org-groote, Homepage: your domain, Callback URL: {origin}/oauth/callback/github" },
    { step: 3, title: "Set Permissions", description: "Repository: Read & Write, Issues: Read & Write, Pull Requests: Read & Write" },
    { step: 4, title: "Generate Private Key", description: "After creation, generate a private key and paste it below" },
    { step: 5, title: "Copy Credentials", description: "Copy the App ID, Client ID, and Client Secret into the fields below" },
  ],
}
```

---

### Phase 4: Update Types

**File:** `external-dashboard/src/features/setup/types.ts`

- Add `stepType?: "service" | "oauth_setup"` to `StepDefinition`
- Add `oauthPlatform?: string` to `StepDefinition`
- Add `instructions?: InstructionStep[]` to `StepDefinition`
- Add `multiline?: boolean` to `FieldDefinition`
- Add new `InstructionStep` type: `{ step: number; title: string; description: string; link?: string }`

---

### Phase 5: Create OAuthSetupStep Component

**New file:** `external-dashboard/src/features/setup/steps/OAuthSetupStep.tsx`

- Renders platform-specific instructions as a numbered step list with external links
- Below instructions, renders credential input fields (Client ID, Client Secret, etc.)
- "Test Connection" button validates credentials via backend
- Uses same save/validate flow as ServiceStep but with instructions UI above the form
- Collapsible instruction panel (expanded by default on first visit)

---

### Phase 6: Update SetupFeature Router

**File:** `external-dashboard/src/features/setup/SetupFeature.tsx`

- If step has `stepType === "oauth_setup"`, render `OAuthSetupStep` instead of `ServiceStep`
- Import the new `OAuthSetupStep` component

---

### Phase 7: Backend Validators for OAuth Credentials

**File:** `dashboard-api/core/setup/validators.py`

- Replace `validate_github(token)` with `validate_github_oauth(app_id, client_id, client_secret)` — verify GitHub App exists via `GET /app` with JWT auth
- Replace `validate_jira(url, email, token)` with `validate_jira_oauth(client_id, client_secret)` — verify via Jira OAuth metadata endpoint
- Replace `validate_slack(bot_token)` with `validate_slack_oauth(client_id, client_secret)` — verify via Slack API
- Keep `validate_sentry` and `validate_anthropic` as-is
- Update `VALIDATOR_MAP`

---

### Phase 8: Credential Storage & Propagation

**File:** `dashboard-api/core/setup/service.py`

- OAuth credentials saved through wizard are stored in `setup_config` table (encrypted with Fernet)
- Add endpoint `GET /api/setup/oauth-credentials/{platform}` for oauth-service to consume

**New file:** `oauth-service/config/credential_loader.py`

- On startup, fetch OAuth credentials from dashboard-api via `http://dashboard-api:5000/api/setup/oauth-credentials/{platform}`
- Fall back to environment variables if API call fails
- Cache in memory, refresh periodically

**File:** `docker-compose.yml`

- Add `depends_on: dashboard-api` to oauth-service
- Update `BASE_URL` env var

---

### Phase 9: Update OAuth Service Settings

**File:** `oauth-service/config/settings.py`

- Make all OAuth credentials optional (loaded from DB at runtime)
- Add `DASHBOARD_API_URL` setting

---

### Phase 10: Update Integrations Page for OAuth Callback

**File:** `external-dashboard/src/features/integrations/IntegrationsFeature.tsx`

- Add `useSearchParams` to detect OAuth callback params (`?oauth_callback=github&success=true`)
- Show success/error toast and refresh OAuth status
- Clear query params after handling

---

### Phase 11: Update IntegrationCard Connect Flow

**File:** `external-dashboard/src/features/integrations/IntegrationCard.tsx`

- "Connect" button calls `POST /oauth/install/{platform}` via nginx proxy
- Response contains redirect URL — open in same window or popup
- Show loading state during OAuth flow

---

### Phase 12: Update Welcome Step

**File:** `external-dashboard/src/features/setup/steps/WelcomeStep.tsx`

- "Configure GitHub token" → "Create GitHub App"
- "Configure Jira token" → "Create Jira OAuth App"
- "Configure Slack token" → "Create Slack App"

---

### Phase 13: Sentry Handling

- Keep Sentry as simple API token step (no OAuth)
- `validate_sentry` unchanged

---

### Implementation Order

1. Phase 4 (Types) — no dependencies
2. Phase 3 (Constants) — depends on Phase 4
3. Phase 5 (OAuthSetupStep component) — depends on Phase 4
4. Phase 6 (SetupFeature router) — depends on Phase 5
5. Phase 12 (Welcome step text) — independent
6. Phase 1 (Nginx proxy) — independent
7. Phase 2 (Callback redirect) — depends on Phase 1
8. Phase 7 (Backend validators) — independent
9. Phase 9 (OAuth service settings) — independent
10. Phase 8 (Credential storage) — depends on Phase 7, 9
11. Phase 10 (Integrations callback) — depends on Phase 2
12. Phase 11 (IntegrationCard) — depends on Phase 10
13. Phase 13 (Sentry) — independent

---

### Files Created (New)

- `external-dashboard/src/features/setup/steps/OAuthSetupStep.tsx`
- `oauth-service/config/credential_loader.py`

### Files Modified

- `external-dashboard/nginx.conf`
- `external-dashboard/src/features/setup/constants.ts`
- `external-dashboard/src/features/setup/types.ts`
- `external-dashboard/src/features/setup/SetupFeature.tsx`
- `external-dashboard/src/features/setup/steps/WelcomeStep.tsx`
- `external-dashboard/src/features/integrations/IntegrationsFeature.tsx`
- `external-dashboard/src/features/integrations/IntegrationCard.tsx`
- `dashboard-api/core/setup/validators.py`
- `dashboard-api/core/setup/service.py`
- `oauth-service/api/routes.py`
- `oauth-service/config/settings.py`
- `dashboard-api/api/oauth_status.py`
- `docker-compose.yml`

---

### Verification Plan

1. `make up` — all services healthy
2. Open `http://localhost:3005/setup` — wizard shows OAuth setup steps with instructions
3. Walk through GitHub OAuth step — instructions render, credential fields work, "Test" validates
4. Complete setup wizard — credentials saved to DB
5. Open `http://localhost:3005/integrations` — "Connect" buttons visible
6. Click "Connect GitHub" — redirects to GitHub OAuth flow
7. After authorization — callback redirects back to integrations page with success toast
8. OAuth status shows "Connected" for the platform
