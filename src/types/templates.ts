export interface TemplateParameter {
  key: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'select';
  default?: any;
  required?: boolean;
  description?: string;
  options?: string[];
}

export interface TemplateMetadata {
  id: string;
  title: string;
  description: string;
  category: string;
  icon?: string;
  connectors: string[];
  required_providers?: string[];
  estimated_time_ms: number;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  featured: boolean;
  tags: string[];
  use_case?: string;
  estimated_steps?: number;
  configurable_parameters?: TemplateParameter[];
  workflow_spec: Record<string, any>;
}

export interface InstantiateTemplateResult {
  workflow_id: string;
  name: string;
  description?: string;
  workflow_json: Record<string, any>;
  nodes: any[];
  edges: any[];
  version_id: string;
  version_number: number;
  template_metadata?: Record<string, any>;
}

