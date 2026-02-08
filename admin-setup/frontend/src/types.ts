export interface SetupStatus {
  is_complete: boolean;
  current_step: string;
  completed_steps: string[];
  skipped_steps: string[];
  progress_percent: number;
}

export interface InfrastructureStatus {
  postgres: { healthy: boolean; message: string };
  redis: { healthy: boolean; message: string };
}

export interface ServiceField {
  key: string;
  label: string;
  placeholder: string;
  is_sensitive: boolean;
  required: boolean;
  helpText?: string;
}

export interface InstructionStep {
  text: string;
  url?: string;
}

export interface StepDefinition {
  id: string;
  title: string;
  description: string;
  category: string;
  fields: ServiceField[];
  instructions: InstructionStep[];
  skippable: boolean;
}

export interface SaveStepRequest {
  configs: Record<string, string>;
  skip?: boolean;
}

export interface ValidateResponse {
  valid: boolean;
  message: string;
}

export interface ExportResponse {
  content: string;
  filename: string;
}

export interface ConfigSummaryItem {
  key: string;
  value: string;
  category: string;
  is_masked: boolean;
}
