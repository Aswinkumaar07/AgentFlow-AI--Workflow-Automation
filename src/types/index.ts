// ─── Shared TypeScript Types ─────────────────────────────────────────────────
// Shapes mirror expected FastAPI response envelopes for future integration.

export type WorkflowStatus = 'success' | 'running' | 'pending' | 'error' | 'cancelled';
export type AgentStatus = 'idle' | 'thinking' | 'executing' | 'done' | 'failed';
export type Theme = 'dark' | 'light' | 'system';

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: WorkflowStatus;
  createdAt: string;
  updatedAt: string;
  lastRun?: string;
  executionCount: number;
  successCount: number;
  tags: string[];
  prompt?: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: 'trigger' | 'action' | 'condition' | 'transform' | 'output';
  status: AgentStatus;
  duration?: number;
  config: Record<string, unknown>;
  output?: unknown;
}

export interface AgentExecution {
  id: string;
  agentName: string;
  status: AgentStatus;
  startedAt: string;
  duration?: number;
  tokens?: number;
  steps: WorkflowStep[];
}

export interface HistoryEntry {
  id: string;
  workflowId: string;
  workflowName: string;
  status: WorkflowStatus;
  triggeredAt: string;
  duration: number;
  trigger: string;
}

export interface AnalyticsStat {
  label: string;
  value: number;
  change: number;
  unit?: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'admin' | 'user' | 'viewer';
  plan: 'free' | 'pro' | 'enterprise';
  createdAt: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  createdAt: string;
}

// FastAPI response envelope
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  total: number;
  page: number;
  pageSize: number;
}
