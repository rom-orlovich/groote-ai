import type { UseQueryResult } from "@tanstack/react-query";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { act } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import type { SetupStatus } from "./types";

vi.mock("./hooks/useSetup");
vi.mock("./components/AuthGate", () => ({
  AuthGate: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("./components/Layout", () => ({
  Layout: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("./components/DashboardView", () => ({
  DashboardView: () => <div data-testid="dashboard-view">ADMIN_DASHBOARD</div>,
}));
vi.mock("./components/StepIndicator", () => ({
  StepIndicator: () => <div data-testid="step-indicator">Steps</div>,
}));
vi.mock("./steps/WelcomeStep", () => ({ WelcomeStep: () => <div>Welcome</div> }));
vi.mock("./steps/ReviewStep", () => ({ ReviewStep: () => <div>Review</div> }));
vi.mock("./steps/ServiceStep", () => ({ ServiceStep: () => <div>Service</div> }));

describe("App", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    vi.clearAllMocks();
  });

  const renderApp = () =>
    act(async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>,
      );
    });

  it("shows wizard when setup is not complete", async () => {
    const { useSetupStatus } = await import("./hooks/useSetup");
    vi.mocked(useSetupStatus).mockReturnValue({
      data: {
        is_complete: false,
        completed_steps: ["welcome"],
        skipped_steps: [],
        current_step: "public_url",
        progress_percent: 16,
      },
    } as unknown as UseQueryResult<SetupStatus>);

    await renderApp();
    await waitFor(() => expect(screen.getByTestId("step-indicator")).toBeInTheDocument());
  });

  it("shows dashboard when setup is complete", async () => {
    const { useSetupStatus } = await import("./hooks/useSetup");
    vi.mocked(useSetupStatus).mockReturnValue({
      data: {
        is_complete: true,
        completed_steps: ["welcome", "public_url", "github", "jira", "slack", "review"],
        skipped_steps: [],
        current_step: "review",
        progress_percent: 100,
      },
    } as unknown as UseQueryResult<SetupStatus>);

    await renderApp();
    await waitFor(() => {
      expect(screen.getByTestId("dashboard-view")).toBeInTheDocument();
      expect(screen.getByText("ADMIN_DASHBOARD")).toBeInTheDocument();
    });
  });

  it("shows nothing while status is loading", async () => {
    const { useSetupStatus } = await import("./hooks/useSetup");
    vi.mocked(useSetupStatus).mockReturnValue({
      data: undefined,
    } as unknown as UseQueryResult<SetupStatus>);

    await renderApp();
    expect(screen.queryByTestId("step-indicator")).not.toBeInTheDocument();
    expect(screen.queryByTestId("dashboard-view")).not.toBeInTheDocument();
  });
});
