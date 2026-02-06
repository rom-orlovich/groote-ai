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

- Runs on port 5001
- Endpoints:
  - `GET /api/setup/status` - Current setup status
  - `POST /api/setup/steps/{step}` - Complete a setup step
  - `POST /api/setup/complete` - Mark setup as complete
  - `POST /api/setup/reset` - Reset setup progress

## Package Manager

- **pnpm only** - `pnpm install`, `pnpm add <pkg>`
- `.npmrc` with `public-hoist-pattern` required for React 19 (see testing.md)
