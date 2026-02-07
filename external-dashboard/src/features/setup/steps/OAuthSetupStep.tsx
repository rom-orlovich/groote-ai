import { CheckCircle, Eye, EyeOff, Loader2, XCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useSaveStep, useStepConfig, useValidateService } from "../hooks/useSetup";
import type { StepDefinition, ValidateResponse } from "../types";
import { InstructionList } from "./InstructionList";

const SENSITIVE_PLACEHOLDER = "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022";

interface OAuthSetupStepProps {
  step: StepDefinition;
  onNext: () => void;
  onSkip?: () => void;
}

export function OAuthSetupStep({ step, onNext, onSkip }: OAuthSetupStepProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [validation, setValidation] = useState<ValidateResponse | null>(null);
  const isInitialized = useRef(false);

  const { data: savedConfig, isLoading: isLoadingConfig } = useStepConfig(step.id);
  const saveStep = useSaveStep();
  const validateService = useValidateService();

  // biome-ignore lint/correctness/useExhaustiveDependencies: reset state when step changes
  useEffect(() => {
    isInitialized.current = false;
    setValues({});
    setValidation(null);
  }, [step.id]);

  useEffect(() => {
    if (savedConfig && !isInitialized.current) {
      const initialValues: Record<string, string> = {};
      for (const config of savedConfig) {
        if (config.is_sensitive && config.value) {
          initialValues[config.key] = SENSITIVE_PLACEHOLDER;
        } else {
          initialValues[config.key] = config.value;
        }
      }
      setValues(initialValues);
      isInitialized.current = true;
    }
  }, [savedConfig]);

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
    const credentials: Record<string, string> = {};
    for (const [key, val] of Object.entries(values)) {
      if (val !== SENSITIVE_PLACEHOLDER) credentials[key] = val;
    }
    validateService.mutate(
      { service: step.validationService, credentials },
      { onSuccess: (result) => setValidation(result) },
    );
  };

  const handleSave = () => {
    saveStep.mutate(
      {
        step: step.id,
        data: {
          configs: step.fields
            .filter((f) => values[f.key]?.trim() && values[f.key] !== SENSITIVE_PLACEHOLDER)
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

  if (isLoadingConfig) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 size={20} className="animate-spin text-orange-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-heading font-black tracking-wider mb-2">{step.title}</h2>
        <p className="text-[10px] text-gray-500 font-mono">{step.description}</p>
      </div>

      {step.instructions && step.instructions.length > 0 && (
        <InstructionList instructions={step.instructions} />
      )}

      {step.webhookMode === "auto" && (
        <div className="flex items-center gap-2 px-3 py-2 text-[10px] font-heading border border-blue-200 dark:border-blue-800 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30">
          WEBHOOKS_AUTO_CONFIGURED — Webhooks are configured automatically when users connect
        </div>
      )}
      {step.webhookMode === "manual" && (
        <div className="flex items-center gap-2 px-3 py-2 text-[10px] font-heading border border-yellow-200 dark:border-yellow-800 text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-950/30">
          MANUAL_WEBHOOK_REQUIRED — Webhook must be configured manually in provider dashboard
        </div>
      )}

      <div className="space-y-4">
        {step.fields.map((field) => (
          <div key={field.key}>
            <label
              htmlFor={`field-${field.key}`}
              className="block text-[10px] font-heading text-gray-400 mb-1.5"
            >
              {field.label}
              {field.required && <span className="text-red-400 ml-1">*</span>}
            </label>
            <div className="relative">
              {field.multiline ? (
                <textarea
                  id={`field-${field.key}`}
                  value={values[field.key] || ""}
                  onChange={(e) => updateValue(field.key, e.target.value)}
                  placeholder={field.placeholder}
                  rows={4}
                  className="w-full px-3 py-2 text-[11px] font-mono bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 focus:border-orange-400 focus:ring-1 focus:ring-orange-400 outline-none transition-colors resize-y"
                />
              ) : (
                <input
                  id={`field-${field.key}`}
                  type={field.sensitive && !showSecrets[field.key] ? "password" : "text"}
                  value={values[field.key] || ""}
                  onChange={(e) => updateValue(field.key, e.target.value)}
                  placeholder={field.placeholder}
                  className="w-full px-3 py-2 text-[11px] font-mono bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 focus:border-orange-400 focus:ring-1 focus:ring-orange-400 outline-none transition-colors"
                />
              )}
              {field.sensitive && !field.multiline && (
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
