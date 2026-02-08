import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { act } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthGate } from "./AuthGate";

vi.mock("../hooks/useSetup");

const { useCheckAuth, useAuth } = await import("../hooks/useSetup");

const mockUseCheckAuth = vi.mocked(useCheckAuth);
const mockUseAuth = vi.mocked(useAuth);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

async function renderAuthGate(
  checkAuthState: { isLoading: boolean; isSuccess: boolean },
  authState: { mutate: ReturnType<typeof vi.fn>; isPending: boolean; isError: boolean },
) {
  mockUseCheckAuth.mockReturnValue(checkAuthState as ReturnType<typeof useCheckAuth>);
  mockUseAuth.mockReturnValue(authState as unknown as ReturnType<typeof useAuth>);
  await act(async () => {
    render(
      <AuthGate>
        <div>Protected Content</div>
      </AuthGate>,
      { wrapper: createWrapper() },
    );
  });
}

describe("AuthGate", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading spinner while checking auth cookie", async () => {
    const mockMutate = vi.fn();
    await renderAuthGate(
      { isLoading: true, isSuccess: false },
      { mutate: mockMutate, isPending: false, isError: false },
    );
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("shows children directly when cookie is valid", async () => {
    await renderAuthGate(
      { isLoading: false, isSuccess: true },
      { mutate: vi.fn(), isPending: false, isError: false },
    );
    expect(screen.getByText("Protected Content")).toBeInTheDocument();
    expect(screen.queryByText("ADMIN_ACCESS")).not.toBeInTheDocument();
  });

  it("shows login form when cookie check fails", async () => {
    await renderAuthGate(
      { isLoading: false, isSuccess: false },
      { mutate: vi.fn(), isPending: false, isError: false },
    );
    expect(screen.getByText("ADMIN_ACCESS")).toBeInTheDocument();
    expect(screen.getByLabelText("ADMIN_SETUP_TOKEN")).toBeInTheDocument();
  });

  it("disables submit button when token is empty", async () => {
    await renderAuthGate(
      { isLoading: false, isSuccess: false },
      { mutate: vi.fn(), isPending: false, isError: false },
    );
    expect(screen.getByRole("button", { name: /AUTHENTICATE/i })).toBeDisabled();
  });

  it("calls auth mutation on form submit with token value", async () => {
    const user = userEvent.setup();
    const mockMutate = vi.fn();
    await renderAuthGate(
      { isLoading: false, isSuccess: false },
      { mutate: mockMutate, isPending: false, isError: false },
    );
    await user.type(screen.getByLabelText("ADMIN_SETUP_TOKEN"), "test-token-123");
    await user.click(screen.getByRole("button", { name: /AUTHENTICATE/i }));
    expect(mockMutate).toHaveBeenCalledWith("test-token-123", expect.any(Object));
  });

  it("shows children after successful authentication", async () => {
    const user = userEvent.setup();
    let onSuccessCallback: (() => void) | undefined;
    const mockMutate = vi.fn((_, options: any) => {
      onSuccessCallback = options?.onSuccess;
    }) as any;
    await renderAuthGate(
      { isLoading: false, isSuccess: false },
      {
        mutate: mockMutate,
        isPending: false,
        isError: false,
      },
    );
    await user.type(screen.getByLabelText("ADMIN_SETUP_TOKEN"), "test-token-123");
    await user.click(screen.getByRole("button", { name: /AUTHENTICATE/i }));
    await act(async () => onSuccessCallback?.());
    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });
});
