---
name: docs-tests-sync
description: Synchronizes documentation with tests across services. Use when updating documentation, adding features, or verifying test coverage matches documented behavior.
---

# Docs-Tests Sync Skill

> Document → Extract Features/Flows → Match Tests → Generate Reports → Update Tests.

## Quick Reference

- **Flow**: See [flow.md](flow.md) for detailed sync workflow
- **Templates**: See [templates.md](templates.md) for output formats

## Core Principle

**Documentation drives tests.** Every documented feature/flow MUST have corresponding tests.

---

## Sync Process

1. **Discover** - Find all services with docs (README.md, ARCHITECTURE.md)
2. **Extract** - Parse features and flows from documentation
3. **Analyze** - Find existing tests and match to features
4. **Report** - Generate coverage report with gaps
5. **Update** - Create/update tests for missing coverage

---

## Feature Extraction Patterns

Extract from documentation:

| Pattern | Source |
|---------|--------|
| `### Core Responsibilities` | Numbered features with `**Name**:` |
| `## API Endpoints` | Table with Method/Path/Description |
| `### {Service} Flow` | Numbered steps (GitHub, Jira, Slack, Sentry) |
| `- \`name\` - description` | Agent/skill definitions |

---

## Coverage Levels

| Level | Criteria | Badge |
|-------|----------|-------|
| TESTED | 2+ related tests | `[TESTED]` |
| PARTIAL | 1 related test | `[PARTIAL]` |
| NEEDS TESTS | 0 tests | `[NEEDS TESTS]` |

---

## Service Discovery

Target directories:
- `api-gateway/` - Webhook handlers
- `agent-engine/` - Task execution
- `dashboard-api/` - Analytics
- `api-services/{github,jira,slack,sentry}-api/` - External APIs
- `mcp-servers/{name}/` - MCP integrations
- `oauth-service/`, `task-logger/`, `gkg-service/`, `llamaindex-service/`, `indexer-worker/`

---

## Test Matching Rules

Match test to feature when:
- Test name contains 2+ keywords from feature name
- Test docstring mentions feature
- Test file name matches service area

---

## Output Files

Generate per service in `{service}/docs/`:
- `ARCHITECTURE.md` - Component diagrams, protocols, data flows (mermaid)
- `features.md` - All features with coverage status
- `flows.md` - All flows with step validation

Generate in root `docs/`:
- `SYNC_REPORT.md` - Master coverage report

---

## Sync Triggers

Run sync when:
- README.md or ARCHITECTURE.md changes
- New tests added
- Feature behavior changes
- Before major releases

---

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Skip undocumented features | Add to README first |
| Write tests without docs | Document behavior first |
| Ignore coverage gaps | Create test suggestions |
| Manual tracking | Auto-generate reports |
