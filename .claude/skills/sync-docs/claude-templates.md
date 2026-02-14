# CLAUDE.md Templates

Per-service-type templates for CLAUDE.md files. See `templates.md` for docs/ templates.

## FastAPI Service (~100-150 lines)

Based on `api-gateway/CLAUDE.md`:

```markdown
# {Service Name}

{1-2 sentence description} (port {port}). {Key technologies}.

## {Primary Feature Category}

- `{endpoint/path}` - {Description}
- `{endpoint/path}` - {Description}

## Processing Flow

1. {Step 1}
2. {Step 2}
3. {Step 3}

## Folder Structure

\`\`\`
{service-dir}/
├── main.py              # FastAPI app entry point
├── routes/              # Route registration
├── {domain}/            # Domain handlers
├── config/              # Settings
└── tests/               # Co-located tests
\`\`\`

## Testing

\`\`\`bash
make test-{service-name}
# Or directly
PYTHONPATH={service-dir}:$PYTHONPATH uv run pytest {service-dir}/tests/ -v
\`\`\`

## Environment Variables

\`\`\`bash
{VAR_NAME}={default_value}
\`\`\`

## Development Rules

- Maximum 300 lines per file
- NO \`any\` types - use strict Pydantic models
- NO comments - self-explanatory code only
- Tests must run fast (< 5 seconds), no real network calls
- Use async/await for all I/O operations
```

## MCP Thin Wrapper (~70 lines)

Based on `mcp-servers/jira-mcp/CLAUDE.md`:

```markdown
# {Service Name} MCP Development Guide

## Overview

Thin MCP wrapper around the {Backend} API service. Exposes {domain} operations as tools for Claude Code CLI and other MCP clients.

## Key Principles

1. **Thin Wrapper** - No business logic, just protocol translation
2. **Passthrough Design** - All parameters passed directly to backend
3. **Formatted Output** - Results formatted for LLM consumption

## Structure

\`\`\`
{service-dir}/
├── main.py         # FastMCP server entry point
├── {name}_mcp.py   # MCP tool definitions
├── config.py       # Settings
└── requirements.txt
\`\`\`

## Adding a New Tool

1. Add tool function in \`{name}_mcp.py\`
2. Ensure corresponding endpoint exists in {Backend} API service

## Testing Locally

\`\`\`bash
docker-compose --profile api up {backend}-api
python main.py
curl http://localhost:{port}/sse
\`\`\`

## Development

- Port: {port}
- Language: Python
- Framework: FastMCP
- Max 300 lines per file, no comments, strict types, async/await for I/O
```

## Frontend (~60 lines)

Based on `external-dashboard/CLAUDE.md`:

```markdown
# {Service Name}

{Description} (port {port}). {Tech stack}.

## Tech Stack

- **{Framework}** with TypeScript
- **{Bundler}** for bundling
- **{CSS}** for styling
- **{Linter}** for linting and formatting

## Folder Structure

\`\`\`
{service-dir}/
├── src/
│   ├── components/    # Reusable UI components
│   ├── features/      # Feature modules
│   ├── hooks/         # Custom hooks
│   └── App.tsx        # Root component
├── {config files}
└── tsconfig.json
\`\`\`

## Key Commands

\`\`\`bash
pnpm install
pnpm dev
pnpm build
pnpm lint:fix
pnpm test
\`\`\`

## Development Rules

- Use pnpm (NOT npm/yarn)
- No \`any\` types
- Maximum 300 lines per file
- No comments in code

## Environment Variables

\`\`\`bash
{VITE_VAR}={default}
\`\`\`
```

## Rust Service (~80 lines)

Based on `knowledge-graph/CLAUDE.md`:

```markdown
# {Service Name}

{Description} (port {port}). {Key technologies}.

## Development

- Port: {port}
- Language: Rust
- Max 300 lines per file, no comments, strict types, async/await for I/O
- Tests: \`cargo test\`

## Directory Structure

- \`src/main.rs\` - Application entry point
- \`src/api/\` - HTTP handlers and routes
- \`src/models/\` - Data models
- \`src/services/\` - Business logic

## Key Commands

\`\`\`bash
cargo build --release
cargo run
cargo test
cargo fmt
cargo clippy
\`\`\`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| \`{path}\` | {METHOD} | {Description} |

## Environment Variables

\`\`\`bash
PORT={port}
{OTHER_VARS}
\`\`\`

## Health Check

\`\`\`bash
curl http://localhost:{port}/health
\`\`\`
```
