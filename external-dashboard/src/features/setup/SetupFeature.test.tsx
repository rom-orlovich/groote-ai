import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { SetupFeature } from "./SetupFeature";
import { mockSetupComplete, mockSetupIncomplete, mockSetupPartial } from "./test/mocks";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

let mockStatus = mockSetupIncomplete;
let mockIsLoading = false;
const mockSaveStepMutate = vi.fn();

vi.mock("./hooks/useSetup", () => ({
  useSetupStatus: () => ({
    data: mockStatus,
    isLoading: mockIsLoading,
  }),
  useSaveStep: () => ({
    mutate: mockSaveStepMutate,
  }),
}));

vi.mock("./steps/WelcomeStep", () => ({
  WelcomeStep: ({ onNext }: { onNext: () => void }) => (
    <div data-testid="welcome-step">
      <button type="button" onClick={onNext} data-testid="welcome-next">
        BEGIN
      </button>
    </div>
  ),
}));

vi.mock("./steps/AIProviderStep", () => ({
  AIProviderStep: ({ onNext }: { onNext: () => void }) => (
    <div data-testid="ai-provider-step">
      <button type="button" onClick={onNext} data-testid="ai-next">
        NEXT
      </button>
    </div>
  ),
}));

vi.mock("./steps/OAuthSetupStep", () => ({
  OAuthSetupStep: ({ onNext }: { onNext: () => void }) => (
    <div data-testid="oauth-step">
      <button type="button" onClick={onNext} data-testid="oauth-next">
        NEXT
      </button>
    </div>
  ),
}));

vi.mock("./steps/ServiceStep", () => ({
  ServiceStep: ({ onNext }: { onNext: () => void }) => (
    <div data-testid="service-step">
      <button type="button" onClick={onNext} data-testid="service-next">
        NEXT
      </button>
    </div>
  ),
}));

vi.mock("./steps/ReviewStep", () => ({
  ReviewStep: ({ onComplete }: { onComplete: () => void }) => (
    <div data-testid="review-step">
      <button type="button" onClick={onComplete} data-testid="review-complete">
        COMPLETE
      </button>
    </div>
  ),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

async function renderSetup() {
  await act(async () => {
    render(<SetupFeature />, { wrapper: createWrapper() });
  });
}

describe("SetupFeature", () => {
  beforeEach(() => {
    mockStatus = mockSetupIncomplete;
    mockIsLoading = false;
    mockNavigate.mockClear();
    mockSaveStepMutate.mockClear();
  });

  describe("loading state", () => {
    test("should show loading spinner when status is loading", async () => {
      mockIsLoading = true;
      await renderSetup();
      expect(document.querySelector(".animate-spin")).not.toBeNull();
    });
  });

  describe("redirect behavior", () => {
    test("should not redirect when setup is incomplete", async () => {
      mockStatus = mockSetupIncomplete;
      await renderSetup();
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    test("should not redirect when setup is complete (reconfiguration)", async () => {
      mockStatus = mockSetupComplete;
      await renderSetup();
      expect(mockNavigate).not.toHaveBeenCalled();
      expect(screen.getByTestId("welcome-step")).toBeInTheDocument();
    });
  });

  describe("step rendering", () => {
    test("should render welcome step at index 0", async () => {
      await renderSetup();
      expect(screen.getByTestId("welcome-step")).toBeInTheDocument();
    });

    test("should render step indicator with all 7 steps", async () => {
      await renderSetup();
      expect(screen.getByText(/STEP_01 OF_07/)).toBeInTheDocument();
    });
  });

  describe("step navigation", () => {
    test("should hide back button when at first step", async () => {
      await renderSetup();
      expect(screen.queryByText("BACK")).not.toBeInTheDocument();
    });

    test("should advance to next step when welcome next is clicked", async () => {
      mockSaveStepMutate.mockImplementation(
        (_args: unknown, options: { onSuccess: () => void }) => {
          options.onSuccess();
        },
      );
      const user = userEvent.setup();
      await renderSetup();

      await user.click(screen.getByTestId("welcome-next"));
      expect(screen.getByTestId("ai-provider-step")).toBeInTheDocument();
      expect(screen.getByText(/STEP_02 OF_07/)).toBeInTheDocument();
    });

    test("should show back button after advancing past first step", async () => {
      mockSaveStepMutate.mockImplementation(
        (_args: unknown, options: { onSuccess: () => void }) => {
          options.onSuccess();
        },
      );
      const user = userEvent.setup();
      await renderSetup();

      await user.click(screen.getByTestId("welcome-next"));
      expect(screen.getByText("BACK")).toBeInTheDocument();
    });

    test("should go back to previous step when back is clicked", async () => {
      mockSaveStepMutate.mockImplementation(
        (_args: unknown, options: { onSuccess: () => void }) => {
          options.onSuccess();
        },
      );
      const user = userEvent.setup();
      await renderSetup();

      await user.click(screen.getByTestId("welcome-next"));
      expect(screen.getByTestId("ai-provider-step")).toBeInTheDocument();

      await user.click(screen.getByText("BACK"));
      expect(screen.getByTestId("welcome-step")).toBeInTheDocument();
    });
  });

  describe("step indicator colors", () => {
    test("should show green for completed steps", async () => {
      mockStatus = mockSetupPartial;
      await renderSetup();
      const indicators = document.querySelectorAll(".h-1");
      const completedIndicators = document.querySelectorAll(".bg-green-500.h-1");
      expect(indicators.length).toBe(7);
      expect(completedIndicators.length).toBe(1);
    });

    test("should show yellow for skipped steps", async () => {
      mockStatus = mockSetupPartial;
      await renderSetup();
      const skippedIndicators = document.querySelectorAll(".bg-yellow-500.h-1");
      expect(skippedIndicators.length).toBe(1);
    });

    test("should show orange for current step", async () => {
      await renderSetup();
      const currentIndicators = document.querySelectorAll(".bg-orange-500.h-1");
      expect(currentIndicators.length).toBe(1);
    });
  });

  describe("reconfiguration mode", () => {
    test("should allow navigation to setup when is_complete is true", async () => {
      mockStatus = mockSetupComplete;
      await renderSetup();
      expect(screen.getByTestId("welcome-step")).toBeInTheDocument();
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    test("should start at step 0 when setup is complete", async () => {
      mockStatus = mockSetupComplete;
      await renderSetup();
      expect(screen.getByText(/STEP_01 OF_07/)).toBeInTheDocument();
    });

    test("should allow editing steps when setup is complete", async () => {
      mockStatus = mockSetupComplete;
      mockSaveStepMutate.mockImplementation(
        (_args: unknown, options: { onSuccess: () => void }) => {
          options.onSuccess();
        },
      );
      const user = userEvent.setup();
      await renderSetup();

      await user.click(screen.getByTestId("welcome-next"));
      expect(screen.getByTestId("ai-provider-step")).toBeInTheDocument();
    });
  });
});
