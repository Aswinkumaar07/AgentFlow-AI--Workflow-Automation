import { apiClient } from './client';
import type {
  AIInsightItem,
  AnalyticsOverview,
  ConnectorHealthItem,
  AnalyticsChartsData,
  AdvancedAnalyticsResponse,
} from '../types/analytics';

export const analyticsApi = {
  getOverview: async (timeFrame: string = '7d'): Promise<AnalyticsOverview> => {
    const res = await apiClient.get<any>(`/analytics/overview?time_frame=${timeFrame}`);
    const data = res.data?.data ?? res.data;
    if (data && typeof data === 'object' && 'total_executions' in data) {
      return data as AnalyticsOverview;
    }
    throw new Error('Invalid overview response payload');
  },

  getConnectorHealth: async (): Promise<ConnectorHealthItem[]> => {
    const res = await apiClient.get<any>('/analytics/connectors');
    const data = res.data?.data ?? res.data;
    if (Array.isArray(data)) {
      return data as ConnectorHealthItem[];
    }
    return [];
  },

  getInsights: async (): Promise<AIInsightItem[]> => {
    const res = await apiClient.get<any>('/analytics/insights');
    const data = res.data?.data ?? res.data;
    if (Array.isArray(data)) {
      return data as AIInsightItem[];
    }
    return [];
  },

  getChartsData: async (timeFrame: string = '7d'): Promise<AnalyticsChartsData | null> => {
    const res = await apiClient.get<any>(`/analytics/charts?time_frame=${timeFrame}`);
    return res.data?.data ?? res.data;
  },

  getAdvancedAnalytics: async (params?: {
    workflow_id?: string;
    version_id?: string;
    time_frame?: string;
    status?: string;
    provider?: string;
    trigger_type?: string;
  }): Promise<AdvancedAnalyticsResponse | null> => {
    const query = new URLSearchParams(params as any).toString();
    const res = await apiClient.get<any>(`/analytics/advanced?${query}`);
    return res.data?.data ?? res.data;
  },

  exportReport: async (format: 'csv' | 'json' = 'csv', workflow_id: string = 'all'): Promise<Blob | null> => {
    const res = await fetch(`/api/v1/analytics/export?format=${format}&workflow_id=${workflow_id}`);
    if (res.ok) {
      return await res.blob();
    }
    return null;
  },

  recordExecution: async (payload: {
    execution_id: string;
    workflow_name?: string;
    status?: string;
    duration_ms?: number;
    retries?: number;
    steps?: Array<Record<string, any>>;
  }): Promise<void> => {
    await apiClient.post('/analytics/record', payload);
  },
};
