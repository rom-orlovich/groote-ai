import { ArrowLeft, Loader2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { SETUP_STEPS } from "./constants";
import { useSaveStep, useSetupStatus } from "./hooks/useSetup";
import { OAuthSetupStep } from "./steps/OAuthSetupStep";
import { ReviewStep } from "./steps/ReviewStep";
import { ServiceStep } from "./steps/ServiceStep";
import { WelcomeStep } from "./steps/WelcomeStep";

function StepIndicator({
  steps,
  currentIndex,
  completedSteps,
  skippedSteps,
}: {
  steps: typeof SETUP_STEPS;
  currentIndex: number;
  completedSteps: string[];
  skippedSteps: string[];
}) {
  return (
    <div className="flex items-center gap-1 mb-8">
      {steps.map((step, idx) => {
        const isCompleted = completedSteps.includes(step.id);
        const isSkipped = skippedSteps.includes(step.id);
        const isCurrent = idx === currentIndex;

        let bgClass = "bg-gray-200 dark:bg-gray-700";
        if (isCompleted) bgClass = "bg-green-500";
        if (isSkipped) bgClass = "bg-yellow-500";
        if (isCurrent) bgClass = "bg-orange-500";

        return (
          <div key={step.id} className="flex items-center gap-1 flex-1">
            <div className={`h-1 flex-1 rounded-full transition-colors ${bgClass}`} />
          </div>
        );
      })}
    </div>
  );
}

export function SetupFeature() {
  const { data: status, isLoading } = useSetupStatus();
  const [currentIndex, setCurrentIndex] = useState(0);
  const navigate = useNavigate();
  const saveStep = useSaveStep();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 size={24} className="animate-spin text-orange-500" />
      </div>
    );
  }

  if (status?.is_complete) {
    navigate("/");
    return null;
  }

  const currentStep = SETUP_STEPS[currentIndex];

  const goNext = () => {
    if (currentIndex < SETUP_STEPS.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const goBack = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleComplete = () => {
    navigate("/");
  };

  const handleWelcomeNext = () => {
    saveStep.mutate(
      { step: "welcome", data: { configs: [], skip: false } },
      { onSuccess: () => goNext() },
    );
  };

  return (
    <div className="min-h-screen bg-background-app flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-heading font-black tracking-widest text-orange-500 mb-1">
            GROOTE_AI
          </h1>
          <p className="text-[10px] font-heading text-gray-400 tracking-wider">
            SETUP_WIZARD {"//"} STEP_{String(currentIndex + 1).padStart(2, "0")} OF_{" "}
            {String(SETUP_STEPS.length).padStart(2, "0")}
          </p>
        </div>

        <StepIndicator
          steps={SETUP_STEPS}
          currentIndex={currentIndex}
          completedSteps={status?.completed_steps || []}
          skippedSteps={status?.skipped_steps || []}
        />

        {currentIndex > 0 && (
          <button
            type="button"
            onClick={goBack}
            className="flex items-center gap-1 text-[10px] font-heading text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 mb-4 transition-colors"
          >
            <ArrowLeft size={12} /> BACK
          </button>
        )}

        <div className="panel animate-in fade-in slide-in-from-right-4 duration-300">
          {currentStep.id === "welcome" && <WelcomeStep onNext={handleWelcomeNext} />}

          {currentStep.id === "review" && status && (
            <ReviewStep status={status} onComplete={handleComplete} />
          )}

          {currentStep.id !== "welcome" &&
            currentStep.id !== "review" &&
            currentStep.stepType === "oauth_setup" && (
              <OAuthSetupStep step={currentStep} onNext={goNext} onSkip={goNext} />
            )}

          {currentStep.id !== "welcome" &&
            currentStep.id !== "review" &&
            currentStep.stepType !== "oauth_setup" && (
              <ServiceStep step={currentStep} onNext={goNext} onSkip={goNext} />
            )}
        </div>

        <div className="text-center mt-6">
          <p className="text-[9px] font-mono text-gray-400">
            Configuration is encrypted and stored in the database.
            <br />
            You can reconfigure anytime from Settings.
          </p>
        </div>
      </div>
    </div>
  );
}
