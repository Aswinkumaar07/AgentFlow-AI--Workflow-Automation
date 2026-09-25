import { apiClient } from './client';
import type { AnalyticsSummary, WorkflowHistoryItem, WorkflowItem } from '../types/workflow';

export const workflowApi = {
  getWorkflows: async (): Promise<{ items: WorkflowItem[]; total: number }> => {
    try {
      const res = await apiClient.get<any>('/workflows');
      const rawData = res.data?.data ?? res.data;
      if (Array.isArray(rawData)) {
        return { items: rawData as WorkflowItem[], total: rawData.length };
      }
      if (rawData && typeof rawData === 'object' && Array.isArray(rawData.items)) {
        const total = typeof rawData.total === 'number' ? rawData.total : rawData.items.length;
        return { items: rawData.items as WorkflowItem[], total };
      }
      return { items: [], total: 0 };
    } catch {
      return { items: [], total: 0 };
    }
  },

  getWorkflowDetails: async (id: string): Promise<WorkflowItem | null> => {
    try {
      const res = await apiClient.get<any>(`/workflows/${id}`);
      const rawData = res.data?.data ?? res.data;
      if (rawData && typeof rawData === 'object') {
        return rawData as WorkflowItem;
      }
      return null;
    } catch {
      return null;
    }
  },

  getHistory: async (): Promise<WorkflowHistoryItem[]> => {
    try {
      const res = await apiClient.get<any>('/history');
      const rawData = res.data?.data ?? res.data;
      if (Array.isArray(rawData)) {
        return rawData as WorkflowHistoryItem[];
      }
      return [];
    } catch (e: any) {
      throw new Error(e?.response?.data?.message || e?.message || 'Failed to fetch execution history telemetry');
    }
  },

  executeWorkflow: async (workflowSpec: Record<string, any>): Promise<any> => {
    try {
      const res = await apiClient.post<any>('/runtime/execute', { workflow: workflowSpec });
      return res.data?.data ?? res.data;
    } catch (e: any) {
      return {
        success: false,
        execution_id: `exec_${Math.random().toString(36).substring(2, 8)}`,
        status: 'FAILED',
        nodes_executed: 0,
        errors: [e.message || 'Execution error'],
      };
    }
  },

  getVersions: async (workflowId: string): Promise<any[]> => {
    try {
      const res = await apiClient.get<any>(`/workflows/${workflowId}/versions`);
      const raw = res.data?.data ?? res.data;
      return Array.isArray(raw) ? raw : [];
    } catch {
      return [];
    }
  },

  createVersion: async (workflowId: string, payload: Record<string, any>): Promise<any> => {
    try {
      const specNodes = payload?.workflow_spec?.nodes;
      const specEdges = payload?.workflow_spec?.edges;
      console.log(
        `[AI-26 DIAGNOSTIC][3. FRONTEND API POST] workflow_id=${workflowId} spec_nodes=${specNodes?.length ?? 'none'} spec_edges=${specEdges?.length ?? 'none'}`
      );
      const res = await apiClient.post<any>(`/workflows/${workflowId}/versions`, payload);
      return res.data?.data ?? res.data;
    } catch (e: any) {
      throw new Error(e.message || 'Failed to create version snapshot');
    }
  },

  restoreVersion: async (workflowId: string, versionId: string): Promise<any> => {
    try {
      const res = await apiClient.post<any>(`/workflows/${workflowId}/versions/${versionId}/restore`);
      return res.data?.data ?? res.data;
    } catch (e: any) {
      throw new Error(e.message || 'Failed to restore version');
    }
  },

  getExecutions: async (workflowId: string): Promise<any[]> => {
    try {
      const res = await apiClient.get<any>(`/workflows/${workflowId}/executions`);
      const raw = res.data?.data ?? res.data;
      return Array.isArray(raw) ? raw : [];
    } catch {
      return [];
    }
  },

  getAnalytics: async (): Promise<AnalyticsSummary> => {
    try {
      const res = await apiClient.get<any>('/analytics');
      const rawData = res.data?.data ?? res.data;
      if (rawData && typeof rawData === 'object' && 'total_workflows' in rawData) {
        return rawData as AnalyticsSummary;
      }
      return {
        total_workflows: 0,
        successful_runs: 0,
        failed_runs: 0,
        active_agents: 0,
        avg_latency_ms: 0,
        monthly_generations: [],
      };
    } catch {
      return {
        total_workflows: 0,
        successful_runs: 0,
        failed_runs: 0,
        active_agents: 0,
        avg_latency_ms: 0,
        monthly_generations: [],
      };
    }
  },

  getWorkflowAnalytics: async (workflowId: string): Promise<any> => {
    try {
      const res = await apiClient.get<any>(`/workflows/${workflowId}/analytics`);
      return res.data?.data ?? res.data;
    } catch {
      return null;
    }
  },

  getSchedules: async (workflowId: string): Promise<any[]> => {
    try {
      const res = await apiClient.get<any>(`/workflows/${workflowId}/schedules`);
      const raw = res.data?.data ?? res.data;
      return Array.isArray(raw) ? raw : [];
    } catch {
      return [];
    }
  },

  createSchedule: async (workflowId: string, payload: Record<string, any>): Promise<any> => {
    try {
      const res = await apiClient.post<any>(`/workflows/${workflowId}/schedules`, payload);
      return res.data?.data ?? res.data;
    } catch (e: any) {
      throw new Error(e.message || 'Failed to create schedule');
    }
  },

  toggleSchedule: async (workflowId: string, scheduleId: string, active: boolean): Promise<any> => {
    try {
      const res = await apiClient.post<any>(`/workflows/${workflowId}/schedules/${scheduleId}/toggle`, { active });
      return res.data?.data ?? res.data;
    } catch (e: any) {
      throw new Error(e.message || 'Failed to toggle schedule');
    }
  },

  runScheduleNow: async (workflowId: string, scheduleId: string): Promise<any> => {
    try {
      const res = await apiClient.post<any>(`/workflows/${workflowId}/schedules/${scheduleId}/run`);
      return res.data?.data ?? res.data;
    } catch (e: any) {
      throw new Error(e.message || 'Failed to run schedule');
    }
  },

  deleteSchedule: async (workflowId: string, scheduleId: string): Promise<any> => {
    try {
      const res = await apiClient.delete<any>(`/workflows/${workflowId}/schedules/${scheduleId}`);
      return res.data?.data ?? res.data;
    } catch (e: any) {
      throw new Error(e.message || 'Failed to delete schedule');
    }
  },

  getFailedHistory: async (): Promise<any[]> => {
    try {
      const res = await apiClient.get<any>('/history/failed');
      const rawData = res.data?.data ?? res.data;
      return Array.isArray(rawData) ? rawData : [];
    } catch {
      return [];
    }
  },

  replayExecution: async (executionId: string): Promise<any> => {
    try {
      const res = await apiClient.post<any>(`/history/${executionId}/replay`);
      return res.data?.data ?? res.data;
    } catch (e: any) {
      throw new Error(e.message || 'Failed to replay execution');
    }
  },
};


