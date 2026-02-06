# Testing Rules (React 19 + Vitest + pnpm)

## pnpm + React 19 Dual Instance Fix

pnpm strict isolation creates separate `react` copies under `.pnpm/react-dom@*/node_modules/react/`, causing "Invalid hook call" errors.

**Fix**: `.npmrc` with:
```
public-hoist-pattern[]=react
public-hoist-pattern[]=react-dom
```
Then run `pnpm install` to rehoist.

## Test Stack

- **Runner**: Vitest 4 + happy-dom (NOT jsdom - better React 19 compat)
- **Library**: React Testing Library
- **Assertions**: Vitest built-in (`expect`, `vi.fn()`, etc.)

## React 19 act() Pattern

RTL's `render()` needs explicit `act()` wrapper for React 19 concurrent rendering:
```tsx
import { act } from "react";
import { render } from "@testing-library/react";

await act(async () => {
  render(<Component />);
});
```

## Vitest Globals

Import `beforeEach`, `describe`, `it`, `expect` from `vitest` explicitly since tsconfig types don't include vitest globals.

## Test Patterns

- Mock hooks with `vi.mock()` at module level
- Wrap renders with `QueryClientProvider` for TanStack Query components
- Mock child components as simple divs with `data-testid`
- Tests MUST run fast (< 5 seconds per file), NO real network calls
