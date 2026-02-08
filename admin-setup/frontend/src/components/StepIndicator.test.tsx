import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { StepIndicator } from "./StepIndicator";

describe("StepIndicator", () => {
  const mockOnStepClick = vi.fn();

  beforeEach(() => {
    mockOnStepClick.mockClear();
  });

  it("renders all step titles", async () => {
    await act(async () => {
      render(
        <StepIndicator
          currentStep="welcome"
          completedSteps={[]}
          skippedSteps={[]}
          onStepClick={mockOnStepClick}
        />,
      );
    });

    expect(screen.getByText("INFRASTRUCTURE")).toBeInTheDocument();
    expect(screen.getByText("PUBLIC URL")).toBeInTheDocument();
    expect(screen.getByText("GITHUB APP")).toBeInTheDocument();
    expect(screen.getByText("JIRA / ATLASSIAN")).toBeInTheDocument();
    expect(screen.getByText("SLACK APP")).toBeInTheDocument();
    expect(screen.getByText("REVIEW & EXPORT")).toBeInTheDocument();
  });

  it("completed steps show as clickable buttons", async () => {
    await act(async () => {
      render(
        <StepIndicator
          currentStep="github"
          completedSteps={["welcome", "public_url"]}
          skippedSteps={[]}
          onStepClick={mockOnStepClick}
        />,
      );
    });

    const welcomeButton = screen.getByRole("button", { name: /INFRASTRUCTURE/i });
    expect(welcomeButton).not.toBeDisabled();
  });

  it("current step has primary styling", async () => {
    await act(async () => {
      render(
        <StepIndicator
          currentStep="public_url"
          completedSteps={["welcome"]}
          skippedSteps={[]}
          onStepClick={mockOnStepClick}
        />,
      );
    });

    const currentButton = screen.getByRole("button", { name: /PUBLIC URL/i });
    expect(currentButton).toHaveClass("border-primary", "text-primary");
  });

  it("clicking a completed step calls onStepClick with step id", async () => {
    const user = userEvent.setup();

    await act(async () => {
      render(
        <StepIndicator
          currentStep="github"
          completedSteps={["welcome", "public_url"]}
          skippedSteps={[]}
          onStepClick={mockOnStepClick}
        />,
      );
    });

    const welcomeButton = screen.getByRole("button", { name: /INFRASTRUCTURE/i });
    await user.click(welcomeButton);

    expect(mockOnStepClick).toHaveBeenCalledWith("welcome");
  });

  it("future steps beyond current are disabled", async () => {
    await act(async () => {
      render(
        <StepIndicator
          currentStep="public_url"
          completedSteps={["welcome"]}
          skippedSteps={[]}
          onStepClick={mockOnStepClick}
        />,
      );
    });

    const futureButton = screen.getByRole("button", { name: /GITHUB APP/i });
    expect(futureButton).toBeDisabled();
  });

  it("clicking a disabled step does NOT call onStepClick", async () => {
    const user = userEvent.setup();

    await act(async () => {
      render(
        <StepIndicator
          currentStep="public_url"
          completedSteps={["welcome"]}
          skippedSteps={[]}
          onStepClick={mockOnStepClick}
        />,
      );
    });

    const futureButton = screen.getByRole("button", { name: /GITHUB APP/i });
    await user.click(futureButton);

    expect(mockOnStepClick).not.toHaveBeenCalled();
  });
});
