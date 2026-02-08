import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { act } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { BrowsePlatform } from "./hooks/useSourceBrowser";
import { ResourcePicker } from "./ResourcePicker";

const mockUseSourceBrowser = vi.fn();

vi.mock("./hooks/useSourceBrowser", () => ({
  useSourceBrowser: (...args: unknown[]) => mockUseSourceBrowser(...args),
}));

const MOCK_RESOURCES = [
  { id: "repo-1", name: "frontend-app", description: "React dashboard", metadata: {} },
  { id: "repo-2", name: "backend-api", description: "FastAPI service", metadata: {} },
  { id: "repo-3", name: "data-pipeline", description: "ETL pipeline", metadata: {} },
];

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

function renderPicker(overrides?: {
  platform?: BrowsePlatform;
  selectedIds?: string[];
  onSelectionChange?: (ids: string[]) => void;
  onBack?: () => void;
  onNext?: () => void;
}) {
  const defaults = {
    platform: "github" as BrowsePlatform,
    selectedIds: [] as string[],
    onSelectionChange: vi.fn(),
    onBack: vi.fn(),
    onNext: vi.fn(),
  };
  const props = { ...defaults, ...overrides };
  return { ...props, result: render(<ResourcePicker {...props} />, { wrapper: createWrapper() }) };
}

describe("ResourcePicker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSourceBrowser.mockReturnValue({
      resources: MOCK_RESOURCES,
      totalCount: 3,
      hasMore: false,
      isLoading: false,
      isError: false,
    });
  });

  it("renders resource list", async () => {
    await act(async () => {
      renderPicker();
    });

    expect(screen.getByText("frontend-app")).toBeDefined();
    expect(screen.getByText("backend-api")).toBeDefined();
    expect(screen.getByText("data-pipeline")).toBeDefined();
  });

  it("handles selection toggle", async () => {
    const onSelectionChange = vi.fn();
    await act(async () => {
      renderPicker({ onSelectionChange });
    });

    const user = userEvent.setup();
    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[0]);

    expect(onSelectionChange).toHaveBeenCalledWith(["repo-1"]);
  });

  it("handles deselection", async () => {
    const onSelectionChange = vi.fn();
    await act(async () => {
      renderPicker({ selectedIds: ["repo-1", "repo-2"], onSelectionChange });
    });

    const user = userEvent.setup();
    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[0]);

    expect(onSelectionChange).toHaveBeenCalledWith(["repo-2"]);
  });

  it("filters resources by search query", async () => {
    await act(async () => {
      renderPicker();
    });

    const user = userEvent.setup();
    const searchInput = screen.getByPlaceholderText("Search github resources...");
    await user.type(searchInput, "frontend");

    expect(screen.getByText("frontend-app")).toBeDefined();
    expect(screen.queryByText("backend-api")).toBeNull();
    expect(screen.queryByText("data-pipeline")).toBeNull();
  });

  it("toggles select all for filtered items", async () => {
    const onSelectionChange = vi.fn();
    await act(async () => {
      renderPicker({ onSelectionChange });
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("SELECT_ALL"));

    expect(onSelectionChange).toHaveBeenCalledWith(["repo-1", "repo-2", "repo-3"]);
  });

  it("toggles deselect all when all filtered are selected", async () => {
    const onSelectionChange = vi.fn();
    await act(async () => {
      renderPicker({
        selectedIds: ["repo-1", "repo-2", "repo-3"],
        onSelectionChange,
      });
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("DESELECT_ALL"));

    expect(onSelectionChange).toHaveBeenCalledWith([]);
  });

  it("disables NEXT button when no items selected", async () => {
    await act(async () => {
      renderPicker({ selectedIds: [] });
    });

    const nextButton = screen.getByText("NEXT").closest("button");
    expect(nextButton?.disabled).toBe(true);
  });

  it("enables NEXT button when items are selected", async () => {
    await act(async () => {
      renderPicker({ selectedIds: ["repo-1"] });
    });

    const nextButton = screen.getByText("NEXT").closest("button");
    expect(nextButton?.disabled).toBe(false);
  });

  it("calls onBack when BACK is clicked", async () => {
    const onBack = vi.fn();
    await act(async () => {
      renderPicker({ onBack });
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("BACK"));

    expect(onBack).toHaveBeenCalledOnce();
  });

  it("renders loading skeleton", async () => {
    mockUseSourceBrowser.mockReturnValue({
      resources: [],
      totalCount: 0,
      hasMore: false,
      isLoading: true,
      isError: false,
    });

    await act(async () => {
      renderPicker();
    });

    expect(screen.queryByText("frontend-app")).toBeNull();
    expect(screen.queryByRole("checkbox")).toBeNull();
  });

  it("renders error state", async () => {
    mockUseSourceBrowser.mockReturnValue({
      resources: [],
      totalCount: 0,
      hasMore: false,
      isLoading: false,
      isError: true,
    });

    await act(async () => {
      renderPicker();
    });

    expect(screen.getByText("FAILED_TO_LOAD_RESOURCES")).toBeDefined();
  });
});
