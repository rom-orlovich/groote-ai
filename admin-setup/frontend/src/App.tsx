import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { AuthGate } from "./components/AuthGate";
import { DashboardView } from "./components/DashboardView";
import { Layout } from "./components/Layout";
import { StepIndicator } from "./components/StepIndicator";
import { STEPS } from "./constants";
import { useSetupStatus } from "./hooks/useSetup";
import { ReviewStep } from "./steps/ReviewStep";
import { ServiceStep } from "./steps/ServiceStep";
import { WelcomeStep } from "./steps/WelcomeStep";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

interface SetupWizardProps {
  status: {
    current_step: string;
    completed_steps: string[];
    skipped_steps: string[];
    is_complete: boolean;
  };
}

function SetupWizard({ status }: SetupWizardProps) {
  const [currentStep, setCurrentStep] = useState<string>(status.current_step || "welcome");
  const [userNavigated, setUserNavigated] = useState(false);

  const activeStep = userNavigated ? currentStep : status.current_step || currentStep;
  const completedSteps = status.completed_steps || [];
  const skippedSteps = status.skipped_steps || [];

  const advanceStep = useCallback(() => {
    const currentIndex = STEPS.findIndex((s) => s.id === activeStep);
    if (currentIndex < STEPS.length - 1) {
      setCurrentStep(STEPS[currentIndex + 1].id);
      setUserNavigated(false);
    }
  }, [activeStep]);

  const navigateToStep = useCallback(
    (stepId: string) => {
      const targetIndex = STEPS.findIndex((s) => s.id === stepId);
      const currentIndex = STEPS.findIndex((s) => s.id === activeStep);
      const isCompleted = completedSteps.includes(stepId) || skippedSteps.includes(stepId);
      if (isCompleted || targetIndex <= currentIndex) {
        setCurrentStep(stepId);
        setUserNavigated(true);
      }
    },
    [activeStep, completedSteps, skippedSteps],
  );

  const stepDef = STEPS.find((s) => s.id === activeStep);

  return (
    <>
      <StepIndicator
        currentStep={activeStep}
        completedSteps={completedSteps}
        skippedSteps={skippedSteps}
        onStepClick={navigateToStep}
      />
      {activeStep === "welcome" && <WelcomeStep onNext={advanceStep} />}
      {activeStep === "review" && (
        <ReviewStep completedSteps={completedSteps} skippedSteps={skippedSteps} />
      )}
      {stepDef && activeStep !== "welcome" && activeStep !== "review" && (
        <ServiceStep step={stepDef} onNext={advanceStep} onSkip={advanceStep} />
      )}
    </>
  );
}

function AdminSetup() {
  const { data: status } = useSetupStatus();
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<"auto" | "wizard" | "dashboard">("auto");

  const handleResetSetup = async () => {
    await fetch("/api/setup/reset", {
      method: "POST",
      credentials: "include",
    });
    queryClient.invalidateQueries({ queryKey: ["setup-status"] });
    setMode("wizard");
  };

  if (!status) return null;

  const showDashboard = mode === "dashboard" || (mode === "auto" && status.is_complete);
  const showWizard = mode === "wizard" || (mode === "auto" && !status.is_complete);

  return (
    <>
      {showDashboard && (
        <DashboardView
          completedSteps={status.completed_steps}
          skippedSteps={status.skipped_steps}
          onResetSetup={handleResetSetup}
          onEditConfiguration={() => setMode("wizard")}
        />
      )}
      {showWizard && <SetupWizard status={status} />}
    </>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthGate>
        <Layout>
          <AdminSetup />
        </Layout>
      </AuthGate>
    </QueryClientProvider>
  );
}
