export interface WorkflowHistoryItem {
  id: string;
  workflow_name: string;
  provider: string;
  status: 'COMPLETED' | 'RUNNING' | 'FAILED' | 'WAITING_FOR_APPROVAL';
  executed_at: string;
  duration_ms: number;
  steps_count: number;
}

export interface WorkflowItem {
  id: string;
  title: string;
  description?: string;
  status: 'active' | 'draft' | 'paused' | 'archived' | string;
  version: number;
  trigger_type: string;
  definition?: {
    nodes?: Array<{ id: string; name?: string; provider?: string; type?: string }>;
    edges?: Array<{ id: string; source: string; target: string }>;
    [key: string]: any;
  };
  owner_id?: string;
  created_at: string;
  updated_at: string;
}

export interface AnalyticsSummary {
  total_workflows: number;
  successful_runs: number;
  failed_runs: number;
  active_agents: number;
  avg_latency_ms: number;
  monthly_generations: Array<{ month: string; count: number }>;
}
