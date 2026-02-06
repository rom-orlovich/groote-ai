import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import type { InfrastructureStatus } from "../types";
import { WelcomeStep } from "./WelcomeStep";

let mockInfraData: InfrastructureStatus | undefined;
let mockInfraLoading = false;
let mockInfraFetching = false;
const mockRefetch = vi.fn();

vi.mock("../hooks/useSetup", () => ({
  useInfrastructure: () => ({
    data: mockInfraData,
    isLoading: mockInfraLoading,
    isFetching: mockInfraFetching,
    refetch: mockRefetch,
  }),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

async function renderWelcome(props: { onNext: () => void; isReconfiguring?: boolean }) {
  await act(async () => {
    render(<WelcomeStep {...props} />, { wrapper: createWrapper() });
  });
}

describe("WelcomeStep", () => {
  beforeEach(() => {
    mockInfraData = undefined;
    mockInfraLoading = false;
    mockInfraFetching = false;
    mockRefetch.mockClear();
  });

  describe("infrastructure status", () => {
    test("should show infrastructure check panel", async () => {
      await renderWelcome({ onNext: vi.fn() });
      expect(screen.getByText("POSTGRESQL")).toBeInTheDocument();
      expect(screen.getByText("REDIS")).toBeInTheDocument();
    });

    test("should disable begin button when infrastructure not ready", async () => {
      mockInfraData = {
        postgres: { healthy: false, message: "Connection refused" },
        redis: { healthy: false, message: "Connection refused" },
      };
      await renderWelcome({ onNext: vi.fn() });
      const button = screen.getByRole("button", { name: /INFRASTRUCTURE_NOT_READY/ });
      expect(button).toBeDisabled();
    });

    test("should enable begin button when infrastructure is ready", async () => {
      mockInfraData = {
        postgres: { healthy: true, message: "Connected" },
        redis: { healthy: true, message: "Connected" },
      };
      await renderWelcome({ onNext: vi.fn() });
      const button = screen.getByRole("button", { name: /BEGIN/ });
      expect(button).not.toBeDisabled();
    });

    test("should call onNext when begin button is clicked", async () => {
      mockInfraData = {
        postgres: { healthy: true, message: "Connected" },
        redis: { healthy: true, message: "Connected" },
      };
      const onNext = vi.fn();
      const user = userEvent.setup();
      await renderWelcome({ onNext });

      await user.click(screen.getByRole("button", { name: /BEGIN/ }));
      expect(onNext).toHaveBeenCalledOnce();
    });
  });

  describe("reconfiguration mode", () => {
    test("should show reconfiguration title when isReconfiguring is true", async () => {
      mockInfraData = {
        postgres: { healthy: true, message: "Connected" },
        redis: { healthy: true, message: "Connected" },
      };
      await renderWelcome({ onNext: vi.fn(), isReconfiguring: true });
      expect(screen.getByText("RECONFIGURE_SYSTEM")).toBeInTheDocument();
    });

    test("should show initial setup title when isReconfiguring is false", async () => {
      await renderWelcome({ onNext: vi.fn() });
      expect(screen.getByText("SYSTEM_INIT")).toBeInTheDocument();
    });

    test("should show reconfiguration description when isReconfiguring is true", async () => {
      mockInfraData = {
        postgres: { healthy: true, message: "Connected" },
        redis: { healthy: true, message: "Connected" },
      };
      await renderWelcome({ onNext: vi.fn(), isReconfiguring: true });
      expect(screen.getByText(/Review and update your existing configuration/)).toBeInTheDocument();
    });

    test("should show reconfigure button text when isReconfiguring is true", async () => {
      mockInfraData = {
        postgres: { healthy: true, message: "Connected" },
        redis: { healthy: true, message: "Connected" },
      };
      await renderWelcome({ onNext: vi.fn(), isReconfiguring: true });
      const button = screen.getByRole("button", { name: /CONTINUE_RECONFIGURE/ });
      expect(button).toBeInTheDocument();
    });
  });
});
