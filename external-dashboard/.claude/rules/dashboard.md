# External Dashboard Rules

## Tech Stack

- **Framework**: React 19
- **State**: Zustand (global), TanStack Query (server state)
- **Routing**: React Router 7
- **Charts**: Recharts
- **Styling**: Tailwind 4
- **Port**: 3005

## Linting

- Uses **Biome** (NOT ESLint)
- Auto-fix: `pnpm lint:fix`
- Check: `pnpm lint`

## Dashboard API

- Dev proxy target: port 5001
- Vite proxies: `/api/*` -> Dashboard API, `/oauth/*` -> OAuth Service, `/webhooks/*` -> API Gateway, `/ws` -> WebSocket
- Endpoints consumed: `/api/metrics`, `/api/tasks`, `/api/conversations`, `/api/webhooks`, `/api/user-settings/*`, `/api/agent-engine/*`

## Package Manager

- **pnpm only** - `pnpm install`, `pnpm add <pkg>`
- `.npmrc` with `public-hoist-pattern` required for React 19 (see testing.md)
