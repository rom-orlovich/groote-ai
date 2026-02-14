---
name: sync-docs
description: Synchronize documentation (README.md, CLAUDE.md, docs/) across all services or a specific service. Reads source code and updates docs to reflect actual functionality, ports, endpoints, and flows.
user_invocable: true
---

# Sync Documentation

Reads source code across Groote AI services and synchronizes documentation to reflect actual functionality. Creates missing docs, updates stale content, and ensures consistency.

## Arguments

- `<service>` (optional): Service name or `all` (default). Examples: `api-gateway`, `jira-mcp`, `external-dashboard`, `all`
- `--audit-only` (optional): Report gaps and stale content without making changes

## Service Registry

See `service-registry.md` for complete list of services, directories, ports, and expected documentation files.

## Required Documentation Per Service

Every service directory must contain:

| File | Purpose |
|------|---------|
| `README.md` | Overview, setup, API endpoints, env vars, Documentation section |
| `CLAUDE.md` | Development guide for Claude Code (port, structure, rules) |
| `docs/ARCHITECTURE.md` | Component diagrams (mermaid), data flow, directory structure |
| `docs/features.md` | Feature descriptions with capability lists |
| `docs/flows.md` | ASCII flow diagrams with numbered processing steps |

## Execution Steps

### Step 1: Discover Target Services

If `<service>` is specified, resolve it to a single service entry from `service-registry.md`.
If `all` or no argument, iterate over every service in the registry.

### Step 2: Read Source Code

For each target service, read the key source files listed in `service-registry.md`:

- **FastAPI services**: `main.py`, `routes/`, `config/`, `models/`, handler files
- **MCP servers**: `*_mcp.py`, `main.py`, `config.py`
- **Frontend**: `src/App.tsx`, `src/features/`, `package.json`, `vite.config.ts`
- **Rust services**: `src/main.rs`, `src/api/`, `src/models/`, `src/services/`, `Cargo.toml`

Extract from source code:
- Port number (from config, Dockerfile, or main.py)
- API endpoints / MCP tools (from route decorators or `@mcp.tool()`)
- Environment variables (from settings classes or env reads)
- Dependencies on other services (from client URLs or imports)
- Data models (from Pydantic models or struct definitions)

### Step 3: Read Existing Documentation

For each service, read all existing docs:
- `README.md`, `CLAUDE.md`
- `docs/ARCHITECTURE.md`, `docs/features.md`, `docs/flows.md`

### Step 4: Compare Source Against Docs

Identify:
- **Missing files**: Required docs that don't exist
- **Stale content**: Port numbers, endpoint lists, tool counts, env vars that don't match source
- **Missing features**: Functionality in source code not mentioned in docs
- **Missing flows**: Processing paths in source code not documented

### Step 5: Create or Update

If `--audit-only`, skip to Step 7.

**Create missing docs** using templates from `templates.md`:
- Match service type (MCP, FastAPI, Frontend, Rust) to appropriate template
- Fill template with actual source code data from Step 2
- Create `docs/` directory if needed

**Update stale docs**:
- Replace outdated port numbers, endpoint lists, tool names
- Add missing features or flows
- Keep existing accurate content intact

### Step 6: Ensure README Documentation Section

Every README must include a Documentation section linking to docs/:

```markdown
## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation
```

### Step 7: Generate Report

Output a summary table:

```
Service              | README | CLAUDE.md | ARCH | features | flows | Status
---------------------|--------|-----------|------|----------|-------|--------
api-gateway          | OK     | OK        | OK   | OK       | OK    | Up to date
github-mcp           | NEW    | NEW       | NEW  | NEW      | NEW   | Created
jira-mcp             | OK     | OK        | NEW  | NEW      | NEW   | Created 3 files
```

## Service Type Classification

| Type | CLAUDE.md Size | Examples |
|------|---------------|----------|
| MCP thin wrapper | ~70 lines | jira-mcp, slack-mcp, gkg-mcp |
| FastAPI service | ~100-150 lines | api-gateway, dashboard-api, oauth-service |
| Frontend | ~60 lines | external-dashboard |
| Rust service | ~80 lines | knowledge-graph |

## Template Reference

- `templates.md` - ARCHITECTURE.md, features.md, flows.md, README templates
- `claude-templates.md` - CLAUDE.md templates per service type (FastAPI, MCP, Frontend, Rust)

## Failure Handling

| Issue | Resolution |
|-------|-----------|
| Source file not found | Skip and note in report |
| Cannot determine port | Check Dockerfile EXPOSE or docker-compose.yml |
| Service has no routes | Minimal docs with available information |
| File exceeds 300 lines | Split content across docs files |
