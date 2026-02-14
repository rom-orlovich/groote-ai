# Implementation Plan — GA-1: Update All Documentation

**Jira Ticket**: [GA-1](https://agents-system-poc.atlassian.net/browse/GA-1)
**Scope**: Large
**Estimated files**: ~45+ documentation files across 23+ locations
**Parallel subtasks**: 6 (grouped by service category)

## Summary

Review and update every README.md, CLAUDE.md, `.claude/CLAUDE.md`, and `docs/` folder across the groote-ai monorepo so they accurately reflect current architecture, setup instructions, environment variables, API endpoints, and inter-service references.

## Shared Context

**Documentation pattern**: Each service follows a consistent README structure:
- Purpose / overview
- Architecture (if applicable)
- Key components
- API endpoints (if applicable)
- Configuration / environment variables
- Commands (run, test, build)
- Dependencies

**CLAUDE.md pattern**: Each CLAUDE.md provides AI agent instructions:
- Service description and role
- Development conventions (max 300 lines/file, no comments, strict types, async/await)
- Port assignments
- Test commands
- Key file locations

**Repo**: `rom-orlovich/groote-ai` on branch `main`

## Current Documentation Inventory

### Existing README.md files (22)
- `README.md` (root)
- `agent-engine/README.md`
- `api-gateway/README.md`
- `api-services/README.md`
- `api-services/github-api/README.md`
- `api-services/jira-api/README.md`
- `api-services/slack-api/README.md`
- `dashboard-api/README.md`
- `external-dashboard/README.md`
- `gkg-service/README.md`
- `indexer-worker/README.md`
- `knowledge-graph/README.md`
- `llamaindex-service/README.md`
- `mcp-servers/README.md`
- `mcp-servers/gkg-mcp/README.md`
- `mcp-servers/jira-mcp/README.md`
- `mcp-servers/knowledge-graph-mcp/README.md`
- `mcp-servers/llamaindex-mcp/README.md`
- `mcp-servers/slack-mcp/README.md`
- `oauth-service/README.md`
- `scripts/audit/README.md`
- `task-logger/README.md`

### Existing CLAUDE.md files (16)
- `.claude/CLAUDE.md` (root)
- `agent-engine/.claude/CLAUDE.md`
- `agent-engine/CLAUDE.md`
- `api-gateway/CLAUDE.md`
- `api-services/CLAUDE.md`
- `dashboard-api/CLAUDE.md`
- `external-dashboard/CLAUDE.md`
- `gkg-service/CLAUDE.md`
- `indexer-worker/CLAUDE.md`
- `llamaindex-service/CLAUDE.md`
- `mcp-servers/CLAUDE.md`
- `mcp-servers/gkg-mcp/CLAUDE.md`
- `mcp-servers/llamaindex-mcp/CLAUDE.md`
- `oauth-service/CLAUDE.md`
- `scripts/audit/.claude/CLAUDE.md`
- `task-logger/CLAUDE.md`

### Existing docs/ files (7)
- `docs/ARCHITECTURE.md`
- `docs/TUNNEL_SETUP.md`
- `docs/SETUP-KNOWLEDGE.md`
- `docs/KNOWLEDGE-LAYER.md`
- `docs/webhook-integration-guide.md`
- `docs/plans/2026-02-12-agent-flag-migration.md`
- `docs/plans/2026-02-13-system-audit-framework.md`

### Missing CLAUDE.md files (need to create)
- `knowledge-graph/CLAUDE.md`
- `api-services/github-api/CLAUDE.md`
- `api-services/jira-api/CLAUDE.md`
- `api-services/slack-api/CLAUDE.md`
- `mcp-servers/knowledge-graph-mcp/CLAUDE.md`
- `mcp-servers/jira-mcp/CLAUDE.md`
- `mcp-servers/slack-mcp/CLAUDE.md`

### Missing README.md files (need to create)
- `admin-setup/README.md`

---

## Subtask 1: Root Level & Docs — `README.md`, `.claude/CLAUDE.md`, `docs/*`

**Can run in parallel with**: Subtask 2, 3, 4, 5, 6
**Blocked by**: nothing
**Owner**: one executor agent

**Files to update**:
1. `README.md` — Review and update root monorepo overview, service list, quickstart, architecture diagram
2. `.claude/CLAUDE.md` — Review and update agent instructions, discovery protocol, file locations
3. `docs/ARCHITECTURE.md` — Update system architecture to reflect all current services
4. `docs/TUNNEL_SETUP.md` — Verify tunnel setup instructions are current
5. `docs/SETUP-KNOWLEDGE.md` — Update knowledge service setup guide
6. `docs/KNOWLEDGE-LAYER.md` — Update knowledge layer documentation
7. `docs/webhook-integration-guide.md` — Update webhook integration guide

**Acceptance criteria**:
- [ ] Root README lists all services with accurate descriptions
- [ ] `.claude/CLAUDE.md` reflects current agent system and discovery protocol
- [ ] `docs/ARCHITECTURE.md` includes all services in the architecture diagram
- [ ] All docs files reference correct ports, URLs, and environment variables
- [ ] Inter-service references are consistent

---

## Subtask 2: Core Services Group A — `agent-engine/`, `api-gateway/`, `dashboard-api/`

**Can run in parallel with**: Subtask 1, 3, 4, 5, 6
**Blocked by**: nothing
**Owner**: one executor agent

**Files to update**:
1. `agent-engine/README.md` — Update purpose, architecture, API endpoints, config, commands
2. `agent-engine/CLAUDE.md` — Update development instructions
3. `agent-engine/.claude/CLAUDE.md` — Update agent instructions
4. `api-gateway/README.md` — Update purpose, routes, config, commands
5. `api-gateway/CLAUDE.md` — Update development instructions
6. `dashboard-api/README.md` — Update purpose, API endpoints, config, commands
7. `dashboard-api/CLAUDE.md` — Update development instructions

**For each service**: Check if a `docs/` folder exists. If it does, review and update all `.md` files inside. If missing but needed, create it.

**Acceptance criteria**:
- [ ] Each README accurately describes the service's current purpose, setup, endpoints, config, and commands
- [ ] Each CLAUDE.md reflects current architecture, conventions, and development instructions
- [ ] Environment variables and ports are correct
- [ ] docs/ folders reviewed and updated if present

---

## Subtask 3: Core Services Group B — `oauth-service/`, `task-logger/`, `external-dashboard/`, `indexer-worker/`

**Can run in parallel with**: Subtask 1, 2, 4, 5, 6
**Blocked by**: nothing
**Owner**: one executor agent

**Files to update**:
1. `oauth-service/README.md` — Update purpose, OAuth flow, config, commands
2. `oauth-service/CLAUDE.md` — Update development instructions
3. `task-logger/README.md` — Update purpose, logging config, commands
4. `task-logger/CLAUDE.md` — Update development instructions
5. `external-dashboard/README.md` — Update purpose, UI components, config, commands
6. `external-dashboard/CLAUDE.md` — Update development instructions
7. `indexer-worker/README.md` — Update purpose, indexing flow, config, commands
8. `indexer-worker/CLAUDE.md` — Update development instructions

**For each service**: Check if a `docs/` folder exists. If it does, review and update all `.md` files inside.

**Acceptance criteria**:
- [ ] Each README accurately describes current service purpose, setup, config, and commands
- [ ] Each CLAUDE.md reflects current conventions
- [ ] Environment variables and ports are correct
- [ ] docs/ folders reviewed and updated if present

---

## Subtask 4: Knowledge Services — `llamaindex-service/`, `gkg-service/`, `knowledge-graph/`

**Can run in parallel with**: Subtask 1, 2, 3, 5, 6
**Blocked by**: nothing
**Owner**: one executor agent

**Files to update**:
1. `llamaindex-service/README.md` — Update purpose, API endpoints, config, commands
2. `llamaindex-service/CLAUDE.md` — Update development instructions
3. `gkg-service/README.md` — Update purpose, API endpoints, config, commands
4. `gkg-service/CLAUDE.md` — Update development instructions
5. `knowledge-graph/README.md` — Update purpose, graph operations, config, commands
6. `knowledge-graph/CLAUDE.md` — **CREATE** (missing) following existing pattern

**For each service**: Check if a `docs/` folder exists. If it does, review and update all `.md` files inside.

**Acceptance criteria**:
- [ ] Each README accurately describes current service purpose, setup, endpoints, config, and commands
- [ ] Each CLAUDE.md reflects current conventions
- [ ] `knowledge-graph/CLAUDE.md` created with correct structure
- [ ] docs/ folders reviewed and updated if present

---

## Subtask 5: API Services & MCP Servers

**Can run in parallel with**: Subtask 1, 2, 3, 4, 6
**Blocked by**: nothing
**Owner**: one executor agent

**Files to update**:
1. `api-services/README.md` — Update overview of all API services
2. `api-services/CLAUDE.md` — Update development instructions
3. `api-services/github-api/README.md` — Update GitHub API service docs
4. `api-services/github-api/CLAUDE.md` — **CREATE** (missing)
5. `api-services/jira-api/README.md` — Update Jira API service docs
6. `api-services/jira-api/CLAUDE.md` — **CREATE** (missing)
7. `api-services/slack-api/README.md` — Update Slack API service docs
8. `api-services/slack-api/CLAUDE.md` — **CREATE** (missing)
9. `mcp-servers/README.md` — Update overview of all MCP servers
10. `mcp-servers/CLAUDE.md` — Update development instructions
11. `mcp-servers/llamaindex-mcp/README.md` — Update docs
12. `mcp-servers/llamaindex-mcp/CLAUDE.md` — Update docs
13. `mcp-servers/gkg-mcp/README.md` — Update docs
14. `mcp-servers/gkg-mcp/CLAUDE.md` — Update docs
15. `mcp-servers/knowledge-graph-mcp/README.md` — Update docs
16. `mcp-servers/knowledge-graph-mcp/CLAUDE.md` — **CREATE** (missing)
17. `mcp-servers/jira-mcp/README.md` — Update docs
18. `mcp-servers/jira-mcp/CLAUDE.md` — **CREATE** (missing)
19. `mcp-servers/slack-mcp/README.md` — Update docs
20. `mcp-servers/slack-mcp/CLAUDE.md` — **CREATE** (missing)

**For each service**: Check if a `docs/` folder exists. If it does, review and update all `.md` files inside.

**Acceptance criteria**:
- [ ] Each README accurately describes current service purpose, setup, endpoints, config, and commands
- [ ] Missing CLAUDE.md files created following existing pattern
- [ ] Existing CLAUDE.md files updated
- [ ] docs/ folders reviewed and updated if present

---

## Subtask 6: Utilities & Scripts — `scripts/audit/`, `admin-setup/`

**Can run in parallel with**: Subtask 1, 2, 3, 4, 5
**Blocked by**: nothing
**Owner**: one executor agent

**Files to update**:
1. `scripts/audit/README.md` — Update audit tool documentation
2. `scripts/audit/.claude/CLAUDE.md` — Update agent instructions for audit tool
3. `admin-setup/README.md` — **CREATE** (missing) describing admin setup purpose and usage

**Acceptance criteria**:
- [ ] `scripts/audit/README.md` describes the audit tool's purpose, usage, and configuration
- [ ] `scripts/audit/.claude/CLAUDE.md` reflects current audit tool conventions
- [ ] `admin-setup/README.md` created (if admin-setup directory exists)

---

## Parallelism Map

```
Subtask 1 (Root & Docs) ──────────┐
Subtask 2 (Core A) ───────────────┤
Subtask 3 (Core B) ───────────────┤──→ Final Review (verify cross-references)
Subtask 4 (Knowledge Services) ───┤
Subtask 5 (API & MCP Servers) ────┤
Subtask 6 (Utilities & Scripts) ──┘
```

All 6 subtasks can run in parallel since each owns distinct files with no overlap.

## Edge Cases & Risks

- **admin-setup/ may not exist**: Check if directory exists before creating README.md. If it doesn't exist, skip.
- **Stale cross-references**: After all subtasks complete, verify inter-service URLs, ports, and references are consistent across all updated files.
- **Large scope**: 45+ files means potential for inconsistencies. Each executor should follow the shared documentation pattern strictly.
- **docs/ folders**: Some services may not have docs/ folders. Only create them if the service has enough complexity to warrant separate documentation.

## Approval

Comment `@agent approve` on this PR to proceed with implementation.
