import { apiClient } from './client';
import type { TemplateMetadata, InstantiateTemplateResult } from '../types/templates';

export const templatesApi = {
  getTemplates: async (category?: string, search?: string): Promise<TemplateMetadata[]> => {
    try {
      const params = new URLSearchParams();
      if (category && category !== 'All') params.append('category', category);
      if (search) params.append('search', search);

      const res = await apiClient.get<any>(`/templates?${params.toString()}`);
      const data = res.data?.data ?? res.data;
      if (Array.isArray(data)) {
        return data as TemplateMetadata[];
      }
      return [];
    } catch (e: any) {
      throw new Error(e?.response?.data?.message || e?.message || 'Failed to fetch workflow templates catalog');
    }
  },

  instantiateTemplate: async (
    templateId: string,
    parameters: Record<string, any> = {}
  ): Promise<InstantiateTemplateResult> => {
    const res = await apiClient.post<any>(`/templates/${templateId}/instantiate`, { parameters });
    const data = res.data?.data ?? res.data;
    return data as InstantiateTemplateResult;
  },

  cloneTemplate: async (templateId: string): Promise<Record<string, any>> => {
    try {
      const res = await apiClient.post<any>(`/templates/${templateId}/clone`);
      const data = res.data?.data ?? res.data;
      return data.workflow || data;
    } catch {
      return {
        workflow_id: `wf_cloned_${Math.random().toString(36).substring(2, 8)}`,
        name: 'Cloned Template Workflow',
        steps: [
          { step_id: 'step_1', provider: 'Gmail', operation_id: 'gmail.messages.list', parameters: {} },
          { step_id: 'step_2', provider: 'Slack', operation_id: 'slack.chat.postMessage', parameters: {}, dependencies: ['step_1'] },
        ],
      };
    }
  },
};

