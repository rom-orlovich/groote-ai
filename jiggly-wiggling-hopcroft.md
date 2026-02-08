# Fix End-to-End Webhook Pipeline

## Context

Webhooks from platforms (GitHub, Jira, Slack) aren't reaching the API gateway, and even if they did, the downstream pipeline (agent routing, response posting) is broken. The user wants: install app → webhooks auto-configure → events flow → agent processes → response posts back.

## Research: How Each Platform Handles Webhooks

### GitHub App
- **Webhook URL is set during app registration** at github.com/settings/apps
- After user installs the app, GitHub **automatically** sends events to that URL
- Can be changed via `PATCH /app/hook/config` (which our code already does)
- **Our code**: `webhook_service.configure_github_app_webhook()` PATCHes the URL after OAuth
- **Likely issue**: If JWT generation fails (wrong private key/app ID), PATCH fails silently and the URL stays at whatever was initially set in GitHub Developer Settings

### Jira OAuth 2.0
- **Dynamic webhooks registered via REST API** after OAuth install
- Requires `manage:jira-webhook` scope (already requested)
- **Webhooks EXPIRE after 30 days** - must be refreshed!
- Limit: 5 per app per user per tenant
- **Our code**: `webhook_service.register_jira_webhook()` registers after OAuth callback
- **Likely issue**: Registration may fail silently, OR webhooks expired and need refresh

### Slack
- **Event Subscriptions URL must be configured manually** at api.slack.com/apps
- Set Request URL to `{PUBLIC_URL}/webhooks/slack` in Event Subscriptions
- **Cannot be auto-registered** via API - one-time manual setup
- **Our code**: Correctly skips auto-registration for Slack

## Implementation Plan

### Phase 1: Webhook Debug & Diagnostics

**WHY**: First verify webhooks can reach the API gateway at all.

#### 1a. Add webhook test endpoint
**MODIFY**: `api-gateway/main.py`
- Add `POST /webhooks/test` that accepts any payload and returns success
- Allows: `curl -X POST {PUBLIC_URL}/webhooks/test -d '{"test":true}'`

#### 1b. Add webhook status endpoint
**NEW**: `oauth-service/api/webhook_status.py`
- `GET /oauth/webhooks/status` - queries each platform for registered webhooks:
  - GitHub: `GET /app/hook/config` (JWT auth) → shows current URL + active status
  - Jira: `GET /ex/jira/{cloud_id}/rest/api/3/webhook` → shows registered webhooks + expiry
  - Slack: return manual config instructions
- **MODIFY**: `oauth-service/main.py` to include the new router

### Phase 2: Fix Webhook Registration Reliability

#### 2a. Better error logging in OAuth callback
**MODIFY**: `oauth-service/api/routes.py` lines 143-172
- Log full webhook result (URL, success, error) at INFO level
- For Slack: log the manual configuration instructions
- Pass error details to frontend in redirect URL

#### 2b. Add Jira webhook refresh mechanism
**NEW**: `oauth-service/services/webhook_refresh.py`
- Jira webhooks expire after 30 days. Add a `refresh_jira_webhooks()` function
- Uses `PUT /ex/jira/{cloud_id}/rest/api/3/webhook/refresh` to extend expiry
- Called by a background check (or dashboard manual trigger)

#### 2c. Ensure webhook secrets match
**Verify** in docker-compose.yml:
- `api-gateway` gets `GITHUB_WEBHOOK_SECRET`, `JIRA_WEBHOOK_SECRET`, `SLACK_WEBHOOK_SECRET`
- `oauth-service` gets `GITHUB_WEBHOOK_SECRET` (used when registering GitHub webhook)
- **Critical**: The secret passed to `PATCH /app/hook/config` must match what `api-gateway` uses to validate incoming webhooks

### Phase 3: Task Router (Production)

**NEW**: `agent-engine/services/task_router.py`

```python
ROUTING_TABLE = {
    "github": {
        "issues": "github-issue-handler",
        "issue_comment": "github-issue-handler",
        "pull_request": "github-pr-review",
        "pull_request_review_comment": "github-pr-review",
    },
    "jira": {
        "jira:issue_created": "jira-code-plan",
        "jira:issue_updated": "jira-code-plan",
        "comment_created": "jira-code-plan",
    },
    "slack": {
        "app_mention": "slack-inquiry",
        "message": "slack-inquiry",
    },
}

def route_task(source: str, event_type: str) -> str | None:
    return ROUTING_TABLE.get(source, {}).get(event_type)
```

### Phase 4: Prompt Builder

**NEW**: `agent-engine/services/prompt_builder.py`

Enriches prompts with metadata agents need to post responses back:
- **GitHub**: repo, issue/PR number, action, labels
- **Jira**: issue key, project key
- **Slack**: channel, thread_ts, user

### Phase 5: Wire into agent-engine

**MODIFY**: `agent-engine/main.py`

#### 5a. `_execute_task` - add routing + enriched prompt
- Import route_task, build_prompt
- Determine agent from source/event_type
- Pass `agents=agent_name` to `run_cli()`

#### 5b. `_process_task` - create conversation for webhook tasks
- For tasks with `source` but no `conversation_id`:
  - POST to `dashboard-api/api/conversations` (already exists at `conversations.py:147`)
  - POST user message with original prompt
  - Store `conversation_id` for result posting

### Phase 6: Tests

- **MODIFY**: `agent-engine/tests/test_task_routing.py` - import from production module
- **NEW**: `agent-engine/tests/test_prompt_builder.py`

## Key Files

| File | Action |
|------|--------|
| `api-gateway/main.py` | MODIFY - add /webhooks/test endpoint |
| `oauth-service/api/webhook_status.py` | NEW - webhook status/debug API |
| `oauth-service/services/webhook_refresh.py` | NEW - Jira webhook refresh |
| `oauth-service/api/routes.py` | MODIFY - better error logging |
| `oauth-service/main.py` | MODIFY - include webhook_status router |
| `agent-engine/services/task_router.py` | NEW - routing table |
| `agent-engine/services/prompt_builder.py` | NEW - enriched prompts |
| `agent-engine/main.py` | MODIFY - wire routing + conversations |
| `agent-engine/tests/test_task_routing.py` | MODIFY - import from production |
| `agent-engine/tests/test_prompt_builder.py` | NEW - tests |

## Verification

```bash
# Unit tests
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/ -v
PYTHONPATH=oauth-service:$PYTHONPATH uv run pytest oauth-service/tests/ -v
uv run ruff check agent-engine/ oauth-service/ api-gateway/

# Webhook connectivity test (services running):
curl -X POST {PUBLIC_URL}/webhooks/test -d '{"test":true}'

# Webhook status check:
curl {PUBLIC_URL}/oauth/webhooks/status

# Full flow test:
curl -X POST http://localhost:8000/webhooks/github \
  -H "X-GitHub-Event: issues" -H "Content-Type: application/json" \
  -d '{"action":"opened","issue":{"title":"test","body":"body","labels":[]},"repository":{"full_name":"test/repo","clone_url":"...","default_branch":"main"}}'
```

## Notes for User

1. **GitHub**: Webhook should auto-configure via `PATCH /app/hook/config`. Verify your `GITHUB_PRIVATE_KEY` and `GITHUB_APP_ID` are correct.
2. **Jira**: Webhook auto-registers via REST API but **expires after 30 days**. We'll add a refresh mechanism.
3. **Slack**: Event Subscriptions URL must be set manually at `api.slack.com/apps` → Event Subscriptions → Request URL = `{PUBLIC_URL}/webhooks/slack`. This cannot be automated.

Sources:
- [GitHub App Webhooks](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/using-webhooks-with-github-apps)
- [Jira Dynamic Webhooks](https://developer.atlassian.com/cloud/jira/platform/webhooks/)
- [Slack Events API](https://docs.slack.dev/apis/events-api/)
