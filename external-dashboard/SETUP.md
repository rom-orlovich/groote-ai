# External Dashboard Setup

The External Dashboard is a React-based monitoring UI for viewing tasks, analytics, and system status.

## Overview

| Property | Value |
|----------|-------|
| Port | 3005 |
| Container | external-dashboard |
| Technology | React 19, TypeScript, Vite, TailwindCSS |

## Prerequisites

- Dashboard API running on port 5000

## Start the Service

### With Docker Compose (Recommended)

```bash
# Starts automatically with other services
make up

# Or start individually
docker-compose up -d external-dashboard
```

### For Local Development

```bash
cd external-dashboard

# Install dependencies
pnpm install

# Set environment variables
export VITE_API_URL=http://localhost:5000
export VITE_WS_URL=ws://localhost:5000/ws

# Run development server
pnpm run dev
```

## Verify Installation

1. Open http://localhost:3005 in your browser
2. On first launch, the dashboard redirects to the Setup Wizard at `/setup`
3. After setup is complete, you will see the Groote AI dashboard

## Configuration

### Environment Variables

For Docker deployment, environment variables are baked into the build. For local development:

```bash
# API endpoint
VITE_API_URL=http://localhost:5000

# WebSocket endpoint
VITE_WS_URL=ws://localhost:5000/ws
```

### Build for Production

```bash
cd external-dashboard
pnpm run build
```

The build output is in `dist/` and served by nginx in the Docker container.

## Features

### Task Monitoring

- Real-time task status updates via WebSocket
- Task list with filtering and sorting
- Task detail view with logs

### Analytics

- Task summary statistics
- Tasks by source (GitHub, Jira, Slack, Sentry)
- Task timeline visualization

### OAuth Management

- View connected OAuth integrations
- Manage data source connections

## Development

### Project Structure

```
external-dashboard/
├── src/
│   ├── features/          # Feature modules
│   │   ├── setup/         # Setup wizard
│   │   ├── integrations/  # OAuth integrations
│   │   ├── tasks/         # Task management
│   │   ├── analytics/     # Analytics views
│   │   └── settings/      # Settings pages
│   ├── hooks/             # React hooks
│   ├── components/        # Shared components
│   └── App.tsx            # Main app component
├── package.json
└── vite.config.ts
```

### Key Technologies

| Technology | Purpose |
|------------|---------|
| React 19 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool |
| TailwindCSS | Styling |
| TanStack Query | Data fetching |
| Zustand | State management |
| Lucide | Icons |

### Available Scripts

```bash
# Development server
pnpm run dev

# Build for production
pnpm run build

# Preview production build
pnpm run preview

# Type checking
pnpm run typecheck

# Linting
pnpm run lint
```

## Troubleshooting

### Dashboard not loading

1. Check Dashboard API is running:
   ```bash
   curl http://localhost:5000/health
   ```

2. Check browser console for errors

3. Verify CORS is configured in Dashboard API

### WebSocket not connecting

1. Check WebSocket URL is correct
2. Verify Dashboard API WebSocket endpoint is working:
   ```bash
   # Use websocat or similar tool
   websocat ws://localhost:5000/ws
   ```

### Blank page after build

1. Check nginx configuration in Dockerfile
2. Verify build completed successfully:
   ```bash
   docker-compose logs external-dashboard
   ```

## Related Documentation

- [Main Setup Guide](../SETUP.md)
- [Dashboard API Setup](../dashboard-api/SETUP.md)
- [Architecture](../docs/ARCHITECTURE.md)
