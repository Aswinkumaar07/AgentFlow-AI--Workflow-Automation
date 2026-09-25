export interface ExecutionTrendItem {
  timestamp: string;
  executions: number;
  failures: number;
  avg_latency_ms?: number;
}

export interface AnalyticsOverview {
  time_frame: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  cancelled_executions?: number;
  success_rate_pct: number;
  avg_duration_ms: number;
  total_retries: number;
  active_workflows: number;
  connected_providers: number;
  ai_generations_count: number;
  execution_trend: ExecutionTrendItem[];
}

export interface ConnectorHealthItem {
  provider: string;
  status: 'HEALTHY' | 'DEGRADED' | 'UNAVAILABLE';
  avg_latency_ms: number;
  success_rate_pct: number;
  call_count: number;
  error_count?: number;
}

export interface AIInsightItem {
  id: string;
  type: string;
  title: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  description: string;
  potential_time_saved_ms: number;
}

export interface AnalyticsChartsData {
  overview: AnalyticsOverview;
  execution_trend: ExecutionTrendItem[];
  connector_health: ConnectorHealthItem[];
  latency_breakdown: Array<{ provider: string; avg_latency_ms: number }>;
  volume_by_provider: Array<{ provider: string; call_count: number }>;
}

export interface HealthScoreInfo {
  status: 'Healthy' | 'At Risk' | 'Degraded';
  score: number;
  reasons: string[];
}

export interface ErrorTrendInfo {
  category: string;
  count: number;
  percentage: number;
  affected_workflows?: string[];
  affected_nodes?: string[];
  recent_occurrence?: string;
}

export interface VersionComparisonInfo {
  version_id: string;
  version_number: number;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  average_duration_ms?: number;
  p50_duration_ms?: number;
  p95_duration_ms?: number;
}

export interface AdvancedAnalyticsResponse {
  workflow_id: string;
  summary: {
    total_executions: number;
    successful_executions: number;
    failed_executions: number;
    waiting_executions: number;
    paused_executions: number;
    cancelled_executions: number;
    blocked_executions: number;
    total_retry_attempts: number;
    nodes_retried: number;
    successful_after_retry: number;
    exhausted_retries: number;
    success_rate?: number | null;
    average_duration_ms?: number | null;
    p50_duration_ms?: number | null;
    p95_duration_ms?: number | null;
  };
  health_score: HealthScoreInfo;
  provider_statistics: Array<{
    provider: string;
    execution_count: number;
    success_rate: number;
    average_duration_ms?: number;
    p50_duration_ms?: number;
    p95_duration_ms?: number;
    retries: number;
  }>;
  node_statistics: Array<{
    node_id: string;
    provider: string;
    operation_id: string;
    execution_count: number;
    success_count: number;
    failure_count: number;
    average_duration_ms?: number;
    p50_duration_ms?: number;
    p95_duration_ms?: number;
  }>;
  error_trends: ErrorTrendInfo[];
  version_comparison: VersionComparisonInfo[];
}
