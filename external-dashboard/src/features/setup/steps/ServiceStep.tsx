import { CheckCircle, Eye, EyeOff, Loader2, XCircle } from "lucide-react";
import { useState } from "react";
import { useSaveStep, useValidateService } from "../hooks/useSetup";
import type { StepDefinition, ValidateResponse } from "../types";

interface ServiceStepProps {
  step: StepDefinition;
  onNext: () => void;
  onSkip?: () => void;
}

export function ServiceStep({ step, onNext, onSkip }: ServiceStepProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [validation, setValidation] = useState<ValidateResponse | null>(null);

  const saveStep = useSaveStep();
  const validateService = useValidateService();

  const updateValue = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }));
    setValidation(null);
  };

  const toggleSecret = (key: string) => {
    setShowSecrets((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const requiredFields = step.fields.filter((f) => f.required);
  const allRequiredFilled = requiredFields.every((f) => values[f.key]?.trim());

  const handleValidate = () => {
    if (!step.validationService) return;
    validateService.mutate(
      { service: step.validationService, credentials: values },
      { onSuccess: (result) => setValidation(result) },
    );
  };

  const handleSave = () => {
    saveStep.mutate(
      {
        step: step.id,
        data: {
          configs: step.fields
            .filter((f) => values[f.key]?.trim())
            .map((f) => ({
              key: f.key,
              value: values[f.key],
              display_name: f.label,
              is_sensitive: f.sensitive,
            })),
          skip: false,
        },
      },
      { onSuccess: () => onNext() },
    );
  };

  const handleSkip = () => {
    saveStep.mutate(
      { step: step.id, data: { configs: [], skip: true } },
      { onSuccess: () => onSkip?.() || onNext() },
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-heading font-black tracking-wider mb-2">{step.title}</h2>
        <p className="text-[10px] text-gray-500 font-mono">{step.description}</p>
      </div>

      <div className="space-y-4">
        {step.fields.map((field) => (
          <div key={field.key}>
            <label className="block text-[10px] font-heading text-gray-400 mb-1.5">
              {field.label}
              {field.required && <span className="text-red-400 ml-1">*</span>}
            </label>
            <div className="relative">
              <input
                type={field.sensitive && !showSecrets[field.key] ? "password" : "text"}
                value={values[field.key] || ""}
                onChange={(e) => updateValue(field.key, e.target.value)}
                placeholder={field.placeholder}
                className="w-full px-3 py-2 text-[11px] font-mono bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 focus:border-orange-400 focus:ring-1 focus:ring-orange-400 outline-none transition-colors"
              />
              {field.sensitive && (
                <button
                  type="button"
                  onClick={() => toggleSecret(field.key)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showSecrets[field.key] ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              )}
            </div>
            {field.helpText && (
              <p className="text-[9px] text-gray-400 mt-1 font-mono">{field.helpText}</p>
            )}
          </div>
        ))}
      </div>

      {step.validationService && (
        <div className="space-y-2">
          <button
            type="button"
            onClick={handleValidate}
            disabled={!allRequiredFilled || validateService.isPending}
            className="w-full py-2 text-[10px] font-heading border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {validateService.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 size={12} className="animate-spin" /> VALIDATING...
              </span>
            ) : (
              "TEST_CONNECTION"
            )}
          </button>

          {validation && (
            <div
              className={`flex items-center gap-2 p-2 text-[10px] font-mono ${
                validation.success
                  ? "text-green-600 bg-green-50 dark:bg-green-900/20"
                  : "text-red-600 bg-red-50 dark:bg-red-900/20"
              }`}
            >
              {validation.success ? <CheckCircle size={12} /> : <XCircle size={12} />}
              {validation.message}
            </div>
          )}
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={!allRequiredFilled || saveStep.isPending}
          className="flex-1 btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {saveStep.isPending ? "SAVING..." : "SAVE_AND_CONTINUE"}
        </button>
        {step.skippable && (
          <button
            type="button"
            onClick={handleSkip}
            disabled={saveStep.isPending}
            className="px-4 py-2 text-[10px] font-heading border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            SKIP
          </button>
        )}
      </div>
    </div>
  );
}
