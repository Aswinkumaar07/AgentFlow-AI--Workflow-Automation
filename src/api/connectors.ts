import { apiClient } from './client';

export type ParameterType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'boolean'
  | 'date'
  | 'select'
  | 'multi_select'
  | 'file'
  | 'json'
  | 'expression'
  | 'password'
  | 'email'
  | 'url'
  | 'array'
  | 'object'
  | 'string'
  | 'kv_pairs';

export interface ParameterOption {
  label: string;
  value: string;
}

export interface ParameterSchema {
  name: string;
  display_name: string;
  type: ParameterType;
  required: boolean;
  description?: string;
  default_value?: any;
  options?: ParameterOption[];
  validation_rule?: string;
}

export interface OperationSchema {
  id: string;
  display_name: string;
  description: string;
  required_parameters: ParameterSchema[];
  optional_parameters: ParameterSchema[];
  default_values: Record<string, any>;
}

export interface ConnectorMetadata {
  provider: string;
  display_name: string;
  icon: string;
  auth_type: string;
  supported_operations: string[];
  operation_schemas: Record<string, OperationSchema>;
  categories: string[];
  version: string;
  documentation_url: string;
}

const unwrap = <T>(res: any): T => res?.data?.data ?? res?.data ?? res;

export const connectorsApi = {
  listConnectors: async (): Promise<ConnectorMetadata[]> => {
    try {
      const res = await apiClient.get<any>('/connectors');
      const data = unwrap<ConnectorMetadata[]>(res);
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  },

  getConnectorDefinition: async (provider: string): Promise<ConnectorMetadata | null> => {
    try {
      const res = await apiClient.get<any>(`/connectors/${encodeURIComponent(provider)}`);
      return unwrap<ConnectorMetadata>(res);
    } catch {
      return null;
    }
  },

  getOperationSchema: async (provider: string, operationId: string): Promise<OperationSchema | null> => {
    try {
      const res = await apiClient.get<any>(`/connectors/${encodeURIComponent(provider)}/${encodeURIComponent(operationId)}`);
      return unwrap<OperationSchema>(res);
    } catch {
      return null;
    }
  },
};
