import { CheckCircle, ExternalLink, Eye, EyeOff, Loader2 } from "lucide-react";
import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";
import { useSaveStep, useStepConfig, useValidateService } from "../hooks/useSetup";
import type { StepDefinition } from "../types";

interface ServiceStepProps {
  step: StepDefinition;
  onNext: () => void;
  onSkip?: () => void;
}

export function ServiceStep({ step, onNext, onSkip }: ServiceStepProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [visibleFields, setVisibleFields] = useState<Record<string, boolean>>({});
  const { data: savedConfig } = useStepConfig(step.id);
  const saveMutation = useSaveStep();
  const validateMutation = useValidateService();

  useEffect(() => {
    validateMutation.reset();
  }, [step.id, validateMutation]);

  const mergedValues = { ...savedConfig, ...values };

  const handleChange = (key: string) => (e: ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, [key]: e.target.value }));
  };

  const toggleVisibility = (key: string) => {
    setVisibleFields((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleValidate = () => {
    validateMutation.mutate({ service: step.id, configs: mergedValues });
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    saveMutation.mutate(
      { stepId: step.id, data: { configs: mergedValues } },
      { onSuccess: onNext },
    );
  };

  const handleSkip = () => {
    saveMutation.mutate(
      { stepId: step.id, data: { skip: true, configs: {} } },
      { onSuccess: onSkip || onNext },
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-heading mb-2">{step.title}</h2>
        <p className="text-[11px] text-gray-400">{step.description}</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <form onSubmit={handleSubmit} className="space-y-4">
          {step.fields.map((field) => (
            <div key={field.key}>
              <label
                htmlFor={`field-${field.key}`}
                className="block text-[10px] font-heading text-gray-400 mb-1"
              >
                {field.label} {field.required && <span className="text-cta">*</span>}
              </label>
              <div className="relative">
                <input
                  id={`field-${field.key}`}
                  type={field.is_sensitive && !visibleFields[field.key] ? "password" : "text"}
                  value={mergedValues[field.key] || ""}
                  onChange={handleChange(field.key)}
                  placeholder={field.placeholder}
                  className="w-full bg-input-bg border border-input-border text-input-text px-3 py-2 text-xs font-mono focus:border-primary focus:outline-none pr-10"
                />
                {field.is_sensitive && (
                  <button
                    type="button"
                    onClick={() => toggleVisibility(field.key)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                  >
                    {visibleFields[field.key] ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                )}
              </div>
              {field.helpText && (
                <p className="text-[9px] text-gray-500 mt-0.5">{field.helpText}</p>
              )}
            </div>
          ))}

          {validateMutation.data && (
            <div
              className={`flex items-center gap-2 p-2.5 text-[10px] border ${
                validateMutation.data.valid
                  ? "border-green-500/20 bg-green-500/5 text-green-400"
                  : "border-red-500/20 bg-red-500/5 text-red-400"
              }`}
            >
              <CheckCircle size={12} />
              <span>{validateMutation.data.message}</span>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleValidate}
              disabled={validateMutation.isPending}
              className="px-4 py-2 text-[10px] font-heading border border-panel-border text-gray-400 hover:border-primary hover:text-primary transition-colors disabled:opacity-50"
            >
              {validateMutation.isPending ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                "VALIDATE"
              )}
            </button>
            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="btn-primary text-[10px] disabled:opacity-50"
            >
              {saveMutation.isPending ? "SAVING..." : "SAVE_AND_CONTINUE"}
            </button>
            {step.skippable && (
              <button
                type="button"
                onClick={handleSkip}
                disabled={saveMutation.isPending}
                className="px-4 py-2 text-[10px] font-heading text-gray-500 hover:text-gray-300 transition-colors"
              >
                SKIP
              </button>
            )}
          </div>
        </form>

        {step.instructions.length > 0 && (
          <div className="panel" data-label="INSTRUCTIONS">
            <ol className="space-y-3">
              {step.instructions.map((instruction, index) => (
                <li
                  key={`${step.id}-instruction-${index}`}
                  className="flex gap-3 text-[11px] text-gray-400"
                >
                  <span className="text-primary font-heading text-[10px] shrink-0">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span>
                    {instruction.text}
                    {instruction.url && (
                      <a
                        href={instruction.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-primary hover:text-secondary ml-1"
                      >
                        <ExternalLink size={10} />
                      </a>
                    )}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}
