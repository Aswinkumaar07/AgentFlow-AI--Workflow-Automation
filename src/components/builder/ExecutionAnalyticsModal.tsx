import React, { useEffect, useState } from 'react';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import { useExecutionStore } from '../../store/useExecutionStore';
import { workflowApi } from '../../api/workflows';
import { analyticsApi } from '../../api/analytics';
import {
  BarChart3,
  X,
  CheckCircle2,
  AlertCircle,
  Clock,
  PauseCircle,
  Activity,
  Zap,
  RotateCw,
  ChevronRight,
  TrendingUp,
  Layers,
  Download,
  ShieldCheck,
  Server,
  FileCode,
} from 'lucide-react';

export interface ExecutionAnalyticsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectExecution: (executionResult: any) => void;
}

export const ExecutionAnalyticsModal: React.FC<ExecutionAnalyticsModalProps> = ({
  isOpen,
  onClose,
  onSelectExecution,
}) => {
  const { workflowId } = useWorkflowStore();
  const [analytics, setAnalytics] = useState<any>(null);
  const [advancedData, setAdvancedData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = () => {
    if (!workflowId) return;
    setLoading(true);
    setError(null);
    Promise.all([
      workflowApi.getWorkflowAnalytics(workflowId),
      analyticsApi.getAdvancedAnalytics({ workflow_id: workflowId, time_frame: '7d' })
    ])
      .then(([basicData, advData]) => {
        if (basicData || advData) {
          setAnalytics(basicData || advData);
          setAdvancedData(advData || basicData);
        } else {
          setError('Failed to load workflow analytics.');
        }
      })
      .catch((err) => {
        setError(err.message || 'Error fetching analytics.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (isOpen) {
      fetchAnalytics();
    }
  }, [isOpen, workflowId]);

  if (!isOpen) return null;

  const handleExport = async (format: 'csv' | 'json') => {
    const blob = await analyticsApi.exportReport(format, workflowId || 'all');
    if (blob) {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics_report_${workflowId || 'all'}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    }
  };

  const handleInspect = (item: any) => {
    workflowApi
      .getExecutions(workflowId)
      .then((executions) => {
        const match = executions.find((ex: any) => ex.execution_id === item.execution_id);
        if (match) {
          const isOk = match.status === 'COMPLETED';
          const isWaiting =
            match.status === 'WAITING' ||
            match.status === 'WAITING_FOR_APPROVAL' ||
            match.status === 'PAUSED';

          const nodesExecuted = match.node_records
            ? Object.keys(match.node_records).length
            : match.nodes_executed || 0;
          const nodeResultsList = match.node_records
            ? Object.entries(match.node_records).map(([nid, rec]: [string, any]) => ({
                node_id: nid,
                operation: rec.operation || 'generic.http.request',
                status: rec.status || 'SUCCESS',
                output: rec.output || {},
                latency_ms: rec.latency || 0,
                retries: rec.retries || 0,
              }))
            : [];

          const telemetryPayload = {
            ok: isOk,
            message: isOk
              ? `✓ Workflow [${match.execution_id}] COMPLETED`
              : isWaiting
              ? `⏸ Workflow [${match.execution_id}] ${match.status}`
              : `✕ Workflow [${match.execution_id}] ${match.status || 'FAILED'}`,
            execution_id: match.execution_id,
            workflow_id: match.workflow_id || workflowId,
            version_id: match.version_id,
            version_number: match.version_number,
            status: match.status,
            nodes_executed: nodesExecuted,
            node_results: nodeResultsList,
            can_resume: Boolean(match.can_resume || isWaiting),
          };

          useExecutionStore
            .getState()
            .applyRealExecutionResult(
              match.execution_id,
              match.status || 'COMPLETED',
              nodeResultsList,
              {}
            );

          onSelectExecution(telemetryPayload);
          onClose();
        }
      })
      .catch(() => {});
  };

  const summary = advancedData?.summary || analytics?.summary || {};
  const healthScore = advancedData?.health_score || { status: 'Healthy', score: 100, reasons: [] };
  const providerStats = advancedData?.provider_statistics || [];
  const errorTrends = advancedData?.error_trends || [];
  const versionComp = advancedData?.version_comparison || [];
  const statusDist = analytics?.status_distribution || {};
  const recentExecutions = analytics?.recent_executions || [];
  const totalRuns = summary.total_executions || 0;

  const formatDuration = (ms: number | null | undefined) => {
    if (ms === null || ms === undefined) return '—';
    if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
    return `${Math.round(ms)}ms`;
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-5xl bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Modal Header */}
        <div className="p-4 px-6 border-b border-border flex items-center justify-between bg-muted/20">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/10 text-primary">
              <BarChart3 className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-foreground flex items-center gap-2">
                Advanced Observability, Analytics & SLA Metrics
              </h3>
              <p className="text-xs text-muted-foreground font-mono">Workflow ID: {workflowId}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleExport('csv')}
              title="Export CSV Report"
              className="px-3 py-1.5 rounded-lg border border-border bg-background hover:bg-muted text-xs font-semibold text-foreground transition flex items-center gap-1.5"
            >
              <Download className="h-3.5 w-3.5" /> CSV
            </button>
            <button
              onClick={() => handleExport('json')}
              title="Export JSON Report"
              className="px-3 py-1.5 rounded-lg border border-border bg-background hover:bg-muted text-xs font-semibold text-foreground transition flex items-center gap-1.5"
            >
              <FileCode className="h-3.5 w-3.5" /> JSON
            </button>
            <button
              onClick={fetchAnalytics}
              disabled={loading}
              title="Refresh Analytics"
              className="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition disabled:opacity-50"
            >
              <RotateCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 flex-1 overflow-y-auto space-y-6">
          {loading && !analytics ? (
            <div className="py-16 text-center space-y-3">
              <RotateCw className="h-8 w-8 text-primary animate-spin mx-auto opacity-70" />
              <p className="text-sm text-muted-foreground">Loading workflow execution analytics…</p>
            </div>
          ) : error ? (
            <div className="py-12 text-center space-y-3">
              <AlertCircle className="h-8 w-8 text-destructive mx-auto" />
              <p className="text-sm font-medium text-destructive">{error}</p>
              <button
                onClick={fetchAnalytics}
                className="px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition"
              >
                Retry
              </button>
            </div>
          ) : totalRuns === 0 ? (
            <div className="py-16 text-center space-y-3">
              <Clock className="h-12 w-12 text-muted-foreground/30 mx-auto" />
              <h4 className="text-base font-semibold text-foreground">No executions recorded yet.</h4>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                Execute your workflow from the builder toolbar to capture performance metrics, P50/P95 latency benchmarks, and provider SLA statistics.
              </p>
            </div>
          ) : (
            <>
              {/* Health Score & Summary KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {/* Health Score Card */}
                <div className={`p-4 rounded-xl border flex flex-col justify-between ${
                  healthScore.status === 'Healthy'
                    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500'
                    : healthScore.status === 'At Risk'
                    ? 'border-amber-500/30 bg-amber-500/10 text-amber-500'
                    : 'border-destructive/30 bg-destructive/10 text-destructive'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider">Health Score</span>
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-3xl font-black font-mono">{healthScore.score}%</p>
                    <p className="text-xs font-bold">{healthScore.status}</p>
                  </div>
                </div>

                {/* Runs */}
                <div className="p-3.5 rounded-xl border border-border bg-background/50 space-y-1">
                  <div className="flex items-center justify-between text-muted-foreground text-xs">
                    <span>Total Runs</span>
                    <Layers className="h-4 w-4 text-primary" />
                  </div>
                  <p className="text-2xl font-bold text-foreground font-mono">{summary.total_executions}</p>
                  <p className="text-[11px] text-muted-foreground">Recorded executions</p>
                </div>

                {/* Success Rate */}
                <div className="p-3.5 rounded-xl border border-border bg-background/50 space-y-1">
                  <div className="flex items-center justify-between text-muted-foreground text-xs">
                    <span>Success Rate</span>
                    <TrendingUp className="h-4 w-4 text-emerald-500" />
                  </div>
                  <p className="text-2xl font-bold text-emerald-500 font-mono">
                    {summary.success_rate !== null ? `${summary.success_rate}%` : '—'}
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    {summary.successful_executions} / {summary.total_executions} passed
                  </p>
                </div>

                {/* Avg & P50 Latency */}
                <div className="p-3.5 rounded-xl border border-border bg-background/50 space-y-1">
                  <div className="flex items-center justify-between text-muted-foreground text-xs">
                    <span>Avg / P50 Latency</span>
                    <Zap className="h-4 w-4 text-amber-500" />
                  </div>
                  <p className="text-2xl font-bold text-foreground font-mono">
                    {formatDuration(summary.average_duration_ms)}
                  </p>
                  <p className="text-[11px] text-muted-foreground">P50: {formatDuration(summary.p50_duration_ms)}</p>
                </div>

                {/* P95 Latency */}
                <div className="p-3.5 rounded-xl border border-border bg-background/50 space-y-1">
                  <div className="flex items-center justify-between text-muted-foreground text-xs">
                    <span>P95 Latency</span>
                    <Clock className="h-4 w-4 text-purple-400" />
                  </div>
                  <p className="text-2xl font-bold text-purple-400 font-mono">
                    {formatDuration(summary.p95_duration_ms)}
                  </p>
                  <p className="text-[11px] text-muted-foreground">95th percentile SLA</p>
                </div>
              </div>

              {/* Health Score Explanations */}
              {healthScore.reasons && healthScore.reasons.length > 0 && (
                <div className="p-3 rounded-xl border border-border bg-muted/20 text-xs space-y-1">
                  <span className="font-bold text-foreground">Health Status Diagnosis:</span>
                  <ul className="list-disc list-inside text-muted-foreground space-y-0.5">
                    {healthScore.reasons.map((r: string, idx: number) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Status Distribution */}
              <div className="p-4 rounded-xl border border-border bg-background/40 space-y-3">
                <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                  <Activity className="h-3.5 w-3.5 text-primary" /> Execution Status Distribution
                </h4>

                <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
                  <div className="p-2.5 rounded-lg border border-emerald-500/20 bg-emerald-500/5 flex flex-col">
                    <span className="text-[11px] text-emerald-500 font-semibold">Completed</span>
                    <span className="text-lg font-bold text-emerald-500 font-mono">
                      {statusDist.COMPLETED || summary.successful_executions || 0}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-destructive/20 bg-destructive/5 flex flex-col">
                    <span className="text-[11px] text-destructive font-semibold">Failed</span>
                    <span className="text-lg font-bold text-destructive font-mono">
                      {statusDist.FAILED || summary.failed_executions || 0}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-amber-500/20 bg-amber-500/5 flex flex-col">
                    <span className="text-[11px] text-amber-500 font-semibold">Waiting</span>
                    <span className="text-lg font-bold text-amber-500 font-mono">
                      {statusDist.WAITING || summary.waiting_executions || 0}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-blue-500/20 bg-blue-500/5 flex flex-col">
                    <span className="text-[11px] text-blue-400 font-semibold">Paused</span>
                    <span className="text-lg font-bold text-blue-400 font-mono">
                      {statusDist.PAUSED || summary.paused_executions || 0}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-purple-500/20 bg-purple-500/5 flex flex-col">
                    <span className="text-[11px] text-purple-400 font-semibold">Blocked</span>
                    <span className="text-lg font-bold text-purple-400 font-mono">
                      {statusDist.BLOCKED || summary.blocked_executions || 0}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-muted-foreground/20 bg-muted/20 flex flex-col">
                    <span className="text-[11px] text-muted-foreground font-semibold">Cancelled</span>
                    <span className="text-lg font-bold text-muted-foreground font-mono">
                      {statusDist.CANCELLED || summary.cancelled_executions || 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* Provider Performance */}
              {providerStats.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                    <Server className="h-3.5 w-3.5 text-primary" /> SaaS Provider SLA Performance
                  </h4>
                  <div className="border border-border rounded-xl overflow-hidden bg-background/30 text-xs">
                    <div className="grid grid-cols-6 p-2.5 bg-muted/40 font-bold text-muted-foreground border-b border-border">
                      <span>Provider</span>
                      <span>Executions</span>
                      <span>Success Rate</span>
                      <span>Avg Latency</span>
                      <span>P95 Latency</span>
                      <span>Retries</span>
                    </div>
                    {providerStats.map((p: any) => (
                      <div key={p.provider} className="grid grid-cols-6 p-2.5 border-b border-border/50 items-center font-mono">
                        <span className="font-bold text-foreground">{p.provider}</span>
                        <span>{p.execution_count}</span>
                        <span className="text-emerald-500 font-bold">{p.success_rate}%</span>
                        <span>{formatDuration(p.average_duration_ms)}</span>
                        <span className="text-purple-400">{formatDuration(p.p95_duration_ms)}</span>
                        <span>{p.retries}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Error Category Trends */}
              {errorTrends.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                    <AlertCircle className="h-3.5 w-3.5 text-destructive" /> Error Category Breakdown
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {errorTrends.map((e: any) => (
                      <div key={e.category} className="p-3 rounded-xl border border-destructive/20 bg-destructive/5 space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-destructive capitalize">{e.category}</span>
                          <span className="font-mono text-xs font-bold">{e.count} event(s) ({e.percentage}%)</span>
                        </div>
                        {e.recent_occurrence && (
                          <p className="text-[11px] font-mono text-muted-foreground truncate">{e.recent_occurrence}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Version Comparison */}
              {versionComp.length > 1 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                    <Layers className="h-3.5 w-3.5 text-primary" /> Workflow Version Comparison
                  </h4>
                  <div className="border border-border rounded-xl overflow-hidden bg-background/30 text-xs">
                    <div className="grid grid-cols-5 p-2.5 bg-muted/40 font-bold text-muted-foreground border-b border-border">
                      <span>Version</span>
                      <span>Runs</span>
                      <span>Success Rate</span>
                      <span>Avg Duration</span>
                      <span>P95 Duration</span>
                    </div>
                    {versionComp.map((v: any) => (
                      <div key={v.version_id} className="grid grid-cols-5 p-2.5 border-b border-border/50 items-center font-mono">
                        <span className="font-bold text-primary">v{v.version_number} ({v.version_id.substring(0, 8)})</span>
                        <span>{v.total_runs}</span>
                        <span className="text-emerald-500 font-bold">{v.success_rate}%</span>
                        <span>{formatDuration(v.average_duration_ms)}</span>
                        <span className="text-purple-400">{formatDuration(v.p95_duration_ms)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent Executions Section */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                  <Clock className="h-3.5 w-3.5 text-primary" /> Recent Executions Activity
                </h4>

                <div className="border border-border rounded-xl overflow-hidden bg-background/30">
                  <div className="divide-y divide-border">
                    {recentExecutions.map((item: any) => {
                      const isCompleted = item.status === 'COMPLETED';
                      const isWaiting =
                        item.status === 'WAITING' ||
                        item.status === 'WAITING_FOR_APPROVAL' ||
                        item.status === 'PAUSED';
                      const verNum = item.version_number
                        ? `v${item.version_number}`
                        : item.version_id || 'v1';
                      const timeStr = item.started_at
                        ? new Date(item.started_at * 1000).toLocaleTimeString()
                        : 'Just now';

                      return (
                        <div
                          key={item.execution_id}
                          className="p-3 flex items-center justify-between hover:bg-muted/30 transition text-xs"
                        >
                          <div className="flex items-center gap-3">
                            <div>
                              {isCompleted ? (
                                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                              ) : isWaiting ? (
                                <PauseCircle className="h-4 w-4 text-amber-500" />
                              ) : (
                                <AlertCircle className="h-4 w-4 text-destructive" />
                              )}
                            </div>
                            <div className="space-y-0.5">
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-bold text-foreground">
                                  {item.execution_id}
                                </span>
                                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary">
                                  {verNum}
                                </span>
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                                    isCompleted
                                      ? 'bg-emerald-500/10 text-emerald-500'
                                      : isWaiting
                                      ? 'bg-amber-500/10 text-amber-500'
                                      : 'bg-destructive/10 text-destructive'
                                  }`}
                                >
                                  {item.status || 'COMPLETED'}
                                </span>
                              </div>
                              <p className="text-[11px] text-muted-foreground">
                                Nodes: {item.nodes_executed} / {item.total_nodes} • {timeStr}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <span className="font-mono text-muted-foreground">
                              {formatDuration(item.duration_ms)}
                            </span>
                            <button
                              onClick={() => handleInspect(item)}
                              className="px-2.5 py-1 rounded bg-muted hover:bg-primary/10 hover:text-primary font-semibold text-[11px] transition flex items-center gap-1"
                            >
                              <span>Inspect</span>
                              <ChevronRight className="h-3 w-3" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
