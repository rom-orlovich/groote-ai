# External Dashboard

Frontend dashboard for Groote AI (port 3005). React 19 + TypeScript + Vite + Tailwind CSS. Displays task status, agent activity, analytics, and provides a chat interface for agent interactions.

## Tech Stack

- **React 19** with TypeScript
- **Vite** for bundling
- **Tailwind CSS 4** for styling
- **Biome** for linting and formatting (NOT ESLint)
- **Vitest** + **happy-dom** for testing
- **React Router 7** for navigation
- **TanStack React Query** for server state
- **Zustand** for global client state
- **Recharts** for data visualization
- **Lucide React** for icons

## Folder Structure

```
external-dashboard/
├── src/
│   ├── components/       # Reusable UI components
│   ├── features/         # Feature-specific modules
│   ├── hooks/            # Custom React hooks
│   ├── layouts/          # Page layouts
│   ├── test/             # Test utilities and setup
│   ├── App.tsx           # Root component
│   └── main.tsx          # Entry point
├── biome.json            # Linter/formatter config
├── vite.config.ts        # Build config
└── tsconfig.json         # TypeScript config
```

## Key Commands

```bash
pnpm install              # Install dependencies
pnpm dev                  # Start dev server (port 3005)
pnpm build                # Production build
pnpm lint                 # Check lint errors
pnpm lint:fix             # Fix lint errors (use this, NOT eslint)
pnpm test                 # Run tests
pnpm test -- -t "name"    # Run specific test
```

## Development Rules

- Use `pnpm` (NOT npm/yarn)
- Use Biome for linting (`pnpm lint:fix`), NOT eslint commands
- No `any` types — use proper TypeScript types
- Tests use happy-dom (NOT jsdom) — React 19 compatibility
- React 19 requires explicit `await act(async () => { render(...) })` for tests
- Maximum 300 lines per file
- No comments in code — self-explanatory naming only

## Environment Variables

```bash
VITE_API_URL=http://localhost:5000      # Dashboard API
VITE_WS_URL=ws://localhost:5000/ws      # WebSocket endpoint
```

## Feature Modules

11 feature modules in `src/features/`:
- overview, analytics, ledger, webhooks, chat, registry
- integrations, sources, settings, install, setup

## Dependencies

- **Dashboard API** (port 5000): REST endpoints and WebSocket for real-time updates
- **OAuth Service** (port 8010): OAuth flows proxied via `/oauth/*`

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation
