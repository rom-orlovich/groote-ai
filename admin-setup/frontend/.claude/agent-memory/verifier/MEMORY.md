# Verifier Agent - Memory

## Admin Setup Service

### Docker Container vs Local Code Mismatch (2026-02-08)
- The Docker container runs an older version of the code. Always check the container's files with `docker exec <container> cat /app/<file>` before testing.
- Compare container env vars with local `.env` using `docker exec <container> env | grep <VAR>`.
- The admin-setup service container name is `groote-ai-admin-setup-1`.
- CONFIRMED: Container on port 8015 only has `/health`, `/`, `/api/setup/status`, `/api/setup/complete` -- missing `/api/auth` and other new endpoints
- Local code has the full set of endpoints including `/api/auth` (cookie-based auth)
- To test properly, either rebuild Docker image or run backend locally with `uv run python -m admin_setup.main`

### Auth Mechanism
- **Container (old)**: Header-based auth via `x-admin-token` header
- **Local code (new)**: Cookie-based auth via `admin_session` cookie set by `POST /api/auth`
- Default container token: `admin-token-change-me` (from docker-compose defaults)
- Local `.env` token: may differ (check `ADMIN_SETUP_TOKEN`)

### Endpoints (Local Code - routes.py)
- `POST /api/auth` - Authenticate, sets cookie
- `GET /api/setup/status` - Setup progress
- `GET /api/setup/infrastructure` - Postgres/Redis health
- `POST /api/setup/steps/{step_id}` - Save step config
- `GET /api/setup/steps/{step_id}/config` - Get step config
- `POST /api/setup/validate/{service_name}` - Validate config (public_url, github, jira, slack)
- `GET /api/setup/export` - Export .env content
- `POST /api/setup/complete` - Mark setup complete
- `POST /api/setup/reset` - Reset setup state

## playwright-cli Tips
- Browser sessions are ephemeral -- chain commands with `&&` to keep session alive
- The `fill` command uses aria-refs but refs can map to wrapper divs, not actual inputs
- Use `click <ref>` then `type <text>` as a reliable alternative to `fill`
- On macOS, use `Meta+a` (not `Control+a`) for select-all in input fields
- Snapshot/screenshot files may be saved in CWD's or repo root's `.playwright-cli/` -- check both with Glob

## General Verification Tips
- Always check OpenAPI spec first: `curl -s http://host/openapi.json`
- When endpoints 404 unexpectedly, compare container code vs local code
- SPA catch-all routes (`/{full_path:path}`) can mask missing API routes - check route registration order

## Port Assignments
- 5173: external-dashboard (Vite dev server)
- 5174: admin-setup frontend (when started manually, avoids conflict)
- 8015: admin-setup backend (Docker)
