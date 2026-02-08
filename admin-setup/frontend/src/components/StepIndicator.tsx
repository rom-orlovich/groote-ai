import { Check } from "lucide-react";
import { STEPS } from "../constants";

interface StepIndicatorProps {
  currentStep: string;
  completedSteps: string[];
  skippedSteps: string[];
  onStepClick: (stepId: string) => void;
}

export function StepIndicator({
  currentStep,
  completedSteps,
  skippedSteps,
  onStepClick,
}: StepIndicatorProps) {
  const currentIndex = STEPS.findIndex((s) => s.id === currentStep);

  return (
    <div className="flex items-center gap-1 mb-8 overflow-x-auto pb-2">
      {STEPS.map((step, index) => {
        const isCompleted = completedSteps.includes(step.id) || skippedSteps.includes(step.id);
        const isCurrent = step.id === currentStep;
        const isClickable = isCompleted || isCurrent || index <= currentIndex;

        return (
          <div key={step.id} className="flex items-center">
            {index > 0 && (
              <div className={`w-8 h-px mx-1 ${isCompleted ? "bg-primary" : "bg-panel-border"}`} />
            )}
            <button
              type="button"
              onClick={() => isClickable && onStepClick(step.id)}
              disabled={!isClickable}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-[9px] font-heading border whitespace-nowrap transition-colors ${
                isCurrent
                  ? "border-primary text-primary bg-primary/10"
                  : isCompleted
                    ? "border-green-500/30 text-green-500 bg-green-500/10 hover:bg-green-500/20 cursor-pointer"
                    : isClickable
                      ? "border-panel-border text-gray-500 hover:border-gray-400 cursor-pointer"
                      : "border-panel-border text-gray-600 opacity-50"
              }`}
            >
              {isCompleted && <Check size={10} />}
              {step.title}
            </button>
          </div>
        );
      })}
    </div>
  );
}
