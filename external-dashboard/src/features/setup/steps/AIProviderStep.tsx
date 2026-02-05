import { CheckCircle, Eye, EyeOff, Loader2, XCircle } from "lucide-react";
import { useState } from "react";
import { useSaveStep, useValidateService } from "../hooks/useSetup";
import type { ProviderMode, ServiceField, StepDefinition, ValidateResponse } from "../types";

interface AIProviderStepProps {
  step: StepDefinition;
  onNext: () => void;
}

const PROVIDER_OPTIONS: { value: ProviderMode; label: string }[] = [
  { value: "claude", label: "CLAUDE" },
  { value: "cursor", label: "CURSOR" },
  { value: "both", label: "BOTH" },
];

function getActiveFields(step: StepDefinition, mode: ProviderMode): ServiceField[] {
  const groups = step.providerGroups ?? [];
  if (mode === "both") return groups.flatMap((g) => g.fields);
  return groups.find((g) => g.provider === mode)?.fields ?? [];
}

function getValidationServices(step: StepDefinition, mode: ProviderMode): string[] {
  const groups = step.providerGroups ?? [];
  if (mode === "both") return groups.map((g) => g.validationService);
  const group = groups.find((g) => g.provider === mode);
  return group ? [group.validationService] : [];
}

export function AIProviderStep({ step, onNext }: AIProviderStepProps) {
  const [mode, setMode] = useState<ProviderMode>("claude");
  const [values, setValues] = useState<Record<string, string>>({});
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [validation, setValidation] = useState<Record<string, ValidateResponse>>({});

  const saveStep = useSaveStep();
  const validateService = useValidateService();

  const activeFields = getActiveFields(step, mode);
  const validationServices = getValidationServices(step, mode);

  const updateValue = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }));
    setValidation({});
  };

  const toggleSecret = (key: string) => {
    setShowSecrets((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleValidate = () => {
    for (const svc of validationServices) {
      validateService.mutate(
        { service: svc, credentials: values },
        { onSuccess: (result) => setValidation((prev) => ({ ...prev, [svc]: result })) },
      );
    }
  };

  const handleSave = () => {
    const configs = activeFields
      .filter((f) => values[f.key]?.trim())
      .map((f) => ({
        key: f.key,
        value: values[f.key],
        display_name: f.label,
        is_sensitive: f.sensitive,
      }));

    configs.push({
      key: "CLI_PROVIDER",
      value: mode,
      display_name: "Provider",
      is_sensitive: false,
    });

    saveStep.mutate(
      { step: step.id, data: { configs, skip: false } },
      { onSuccess: () => onNext() },
    );
  };

  const validationResults = Object.values(validation);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-heading font-black tracking-wider mb-2">{step.title}</h2>
        <p className="text-[10px] text-gray-500 font-mono">{step.description}</p>
      </div>

      <div>
        <label className="block text-[10px] font-heading text-gray-400 mb-2">
          SELECT_PROVIDER
        </label>
        <div className="grid grid-cols-3 gap-2">
          {PROVIDER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => { setMode(opt.value); setValidation({}); }}
              className={`py-2.5 text-[11px] font-heading tracking-wider border transition-colors ${
                mode === opt.value
                  ? "border-orange-500 bg-orange-500/10 text-orange-500"
                  : "border-gray-200 dark:border-gray-700 text-gray-400 hover:border-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {activeFields.map((field) => (
          <div key={field.key}>
            <label
              htmlFor={`field-${field.key}`}
              className="block text-[10px] font-heading text-gray-400 mb-1.5"
            >
              {field.label}
              {field.required && <span className="text-red-400 ml-1">*</span>}
            </label>
            <div className="relative">
              <input
                id={`field-${field.key}`}
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

      <div className="space-y-2">
        <button
          type="button"
          onClick={handleValidate}
          disabled={validateService.isPending}
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

        {validationResults.map((result) => (
          <div
            key={result.service}
            className={`flex items-center gap-2 p-2 text-[10px] font-mono ${
              result.success
                ? "text-green-600 bg-green-50 dark:bg-green-900/20"
                : "text-red-600 bg-red-50 dark:bg-red-900/20"
            }`}
          >
            {result.success ? <CheckCircle size={12} /> : <XCircle size={12} />}
            {result.message}
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={handleSave}
        disabled={saveStep.isPending}
        className="w-full btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {saveStep.isPending ? "SAVING..." : "SAVE_AND_CONTINUE"}
      </button>
    </div>
  );
}
