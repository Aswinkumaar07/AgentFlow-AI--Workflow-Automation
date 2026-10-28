export interface AIGenerateRequest {
  prompt: string;
}

export interface AIGenerateStep {
  step_id: string;
  provider: string;
  provider_name?: string;
  operation_id: string;
  parameters: Record<string, any>;
  dependencies?: string[];
}

export interface AIGenerateResponse {
  user_prompt?: string;
  goal?: string;
  workflow_id?: string;
  name?: string;
  services?: string[];
  workflow_json?: {
    title?: string;
    description?: string;
    intent?: string;
    trigger?: Record<string, any>;
    nodes?: any[];
    edges?: any[];
  };
  steps?: AIGenerateStep[];
  validation_report?: Record<string, any>;
  is_valid?: boolean;
  is_repaired?: boolean;
  repair_report?: Record<string, any>;
  execution_metadata?: Record<string, any>;
  logs?: string[];
  schedule?: any;
}
