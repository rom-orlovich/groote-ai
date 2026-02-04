export interface SetupStatus {
  is_complete: boolean;
  current_step: string;
  completed_steps: string[];
  skipped_steps: string[];
  progress_percent: number;
  total_steps: number;
  steps: string[];
}

export interface StepConfigItem {
  key: string;
  value: string;
  display_name: string;
  is_sensitive: boolean;
}

export interface SaveStepRequest {
  configs: StepConfigItem[];
  skip: boolean;
}

export interface SaveStepResponse {
  success: boolean;
  step: string;
  action: string;
  current_step: string;
  progress_percent: number;
}

export interface ValidateResponse {
  service: string;
  success: boolean;
  message: string;
  details: Record<string, string> | null;
}

export interface InfrastructureStatus {
  postgres: { healthy: boolean; message: string };
  redis: { healthy: boolean; message: string };
}

export interface ServiceField {
  key: string;
  label: string;
  placeholder: string;
  sensitive: boolean;
  required: boolean;
  helpText?: string;
}

export interface StepDefinition {
  id: string;
  title: string;
  description: string;
  icon: string;
  skippable: boolean;
  validationService?: string;
  fields: ServiceField[];
}
