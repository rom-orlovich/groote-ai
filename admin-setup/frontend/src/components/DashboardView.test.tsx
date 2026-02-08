import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { act } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DashboardView } from "./DashboardView";

vi.mock("../hooks/useSetup");
vi.mock("./ServiceCard", () => ({
  ConfigSummary: ({ title, status }: { title: string; status: string }) => (
    <div data-testid={`config-summary-${title}`}>{status}</div>
  ),
}));

const { useConfigSummary, useExportConfig } = await import("../hooks/useSetup");

const mockUseConfigSummary = vi.mocked(useConfigSummary);
const mockUseExportConfig = vi.mocked(useExportConfig);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const defaultProps = {
  completedSteps: ["public_url", "github"],
  skippedSteps: ["jira"],
  onResetSetup: vi.fn(),
  onEditConfiguration: vi.fn(),
};

async function renderDashboard(props = defaultProps) {
  await act(async () => {
    render(<DashboardView {...props} />, { wrapper: createWrapper() });
  });
}

describe("DashboardView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseConfigSummary.mockReturnValue({
      data: [],
    } as unknown as ReturnType<typeof useConfigSummary>);
    mockUseExportConfig.mockReturnValue({
      data: undefined,
      refetch: vi.fn().mockResolvedValue({ data: undefined }),
    } as unknown as ReturnType<typeof useExportConfig>);
  });

  it("renders SETUP_COMPLETE heading", async () => {
    await renderDashboard();
    expect(screen.getByText("SETUP_COMPLETE")).toBeInTheDocument();
  });

  it("renders config summaries for completed and skipped steps", async () => {
    await renderDashboard();
    expect(screen.getByTestId("config-summary-PUBLIC URL")).toBeInTheDocument();
    expect(screen.getByTestId("config-summary-GITHUB APP")).toBeInTheDocument();
    expect(screen.getByTestId("config-summary-JIRA / ATLASSIAN")).toBeInTheDocument();
    expect(screen.queryByTestId("config-summary-SLACK APP")).not.toBeInTheDocument();
  });

  it("renders export buttons", async () => {
    await renderDashboard();
    expect(screen.getByRole("button", { name: /EXPORT_\.ENV/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /COPY_TO_CLIPBOARD/i })).toBeInTheDocument();
  });

  it("renders next steps checklist", async () => {
    await renderDashboard();
    expect(screen.getByText("NEXT_STEPS")).toBeInTheDocument();
    expect(screen.getByText(/make up/)).toBeInTheDocument();
  });

  it("calls onResetSetup when RESET_SETUP button is clicked", async () => {
    const user = userEvent.setup();
    await renderDashboard();
    await user.click(screen.getByRole("button", { name: /RESET_SETUP/i }));
    expect(defaultProps.onResetSetup).toHaveBeenCalledOnce();
  });

  it("calls onEditConfiguration when EDIT_CONFIGURATION button is clicked", async () => {
    const user = userEvent.setup();
    await renderDashboard();
    await user.click(screen.getByRole("button", { name: /EDIT_CONFIGURATION/i }));
    expect(defaultProps.onEditConfiguration).toHaveBeenCalledOnce();
  });
});
