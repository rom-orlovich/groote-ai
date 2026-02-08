import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { act } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AddSourceModal } from "./AddSourceModal";

const mockUseSourceTypes = vi.fn();
const mockUseSourceBrowser = vi.fn();

vi.mock("./hooks/useSources", () => ({
  useSourceTypes: () => mockUseSourceTypes(),
}));

vi.mock("./hooks/useSourceBrowser", () => ({
  useSourceBrowser: (...args: unknown[]) => mockUseSourceBrowser(...args),
}));

const CONNECTED_GITHUB = {
  source_type: "github",
  name: "GitHub",
  oauth_platform: "github",
  oauth_connected: true,
  oauth_required: true,
  description: "GitHub repositories",
};

const DISCONNECTED_JIRA = {
  source_type: "jira",
  name: "Jira",
  oauth_platform: "jira",
  oauth_connected: false,
  oauth_required: true,
  description: "Jira projects",
};

const CONNECTED_CONFLUENCE = {
  source_type: "confluence",
  name: "Confluence",
  oauth_platform: "confluence",
  oauth_connected: true,
  oauth_required: true,
  description: "Confluence spaces",
};

const MOCK_GITHUB_RESOURCES = [
  { id: "owner/repo-a", name: "repo-a", description: "First repo", metadata: {} },
  { id: "owner/repo-b", name: "repo-b", description: "Second repo", metadata: {} },
];

const MOCK_CONFLUENCE_RESOURCES = [
  { id: "ENG", name: "ENG", description: "Engineering space", metadata: {} },
  { id: "DOCS", name: "DOCS", description: "Documentation space", metadata: {} },
];

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

function renderModal(overrides?: { onSubmit?: (req: unknown) => void; onClose?: () => void }) {
  const defaults = {
    isOpen: true,
    onClose: vi.fn(),
    onSubmit: vi.fn(),
    isSubmitting: false,
  };
  const props = { ...defaults, ...overrides };
  return { ...props, result: render(<AddSourceModal {...props} />, { wrapper: createWrapper() }) };
}

describe("AddSourceModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSourceTypes.mockReturnValue({
      data: [CONNECTED_GITHUB, DISCONNECTED_JIRA, CONNECTED_CONFLUENCE],
      isLoading: false,
    });
    mockUseSourceBrowser.mockReturnValue({
      resources: [],
      totalCount: 0,
      hasMore: false,
      isLoading: false,
      isError: false,
    });
  });

  it("shows browse step after selecting connected platform", async () => {
    await act(async () => {
      renderModal();
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("GitHub"));

    expect(screen.getByText("BROWSE_RESOURCES")).toBeDefined();
  });

  it("skips browse for disconnected platform", async () => {
    await act(async () => {
      renderModal();
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("Jira"));

    expect(screen.getByText("CONFIGURE_SOURCE")).toBeDefined();
    expect(screen.getByText("OAUTH_NOT_CONNECTED")).toBeDefined();
  });

  it("auto-populates GitHub include_patterns from browse selection", async () => {
    mockUseSourceBrowser.mockReturnValue({
      resources: MOCK_GITHUB_RESOURCES,
      totalCount: 2,
      hasMore: false,
      isLoading: false,
      isError: false,
    });

    await act(async () => {
      renderModal();
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("GitHub"));

    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[0]);
    await user.click(checkboxes[1]);
    await user.click(screen.getByText("NEXT"));

    const includeInput = screen.getByPlaceholderText("owner/repo, owner/repo-*");
    expect((includeInput as HTMLInputElement).value).toBe("owner/repo-a, owner/repo-b");
  });

  it("auto-populates Confluence spaces from browse selection", async () => {
    mockUseSourceBrowser.mockReturnValue({
      resources: MOCK_CONFLUENCE_RESOURCES,
      totalCount: 2,
      hasMore: false,
      isLoading: false,
      isError: false,
    });

    await act(async () => {
      renderModal();
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("Confluence"));

    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[0]);
    await user.click(screen.getByText("NEXT"));

    const spacesInput = screen.getByPlaceholderText("ENG, DOCS, WIKI");
    expect((spacesInput as HTMLInputElement).value).toBe("ENG");
  });

  it("resets state on close", async () => {
    const onClose = vi.fn();
    await act(async () => {
      renderModal({ onClose });
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("GitHub"));
    expect(screen.getByText("BROWSE_RESOURCES")).toBeDefined();

    const closeButton = screen.getByRole("button", { name: "" });
    await user.click(closeButton);

    expect(onClose).toHaveBeenCalledOnce();
  });
});
