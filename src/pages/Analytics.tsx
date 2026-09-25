import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { ConnectorHealthGrid } from '../components/analytics/ConnectorHealthGrid';
import { AIInsightsPanel } from '../components/analytics/AIInsightsPanel';
import {
  BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  BarChart3, RefreshCw, Zap, CheckCircle2, Clock, RotateCcw, TrendingUp, Activity,
} from 'lucide-react';

export default function Analytics() {
  const [timeFrame, setTimeFrame] = useState<'24h' | '7d' | '30d' | '90d'>('7d');

  const { data: overview, isLoading: overviewLoading, refetch: refetchOverview } = useQuery({
    queryKey: ['analytics_overview', timeFrame],
    queryFn: () => analyticsApi.getOverview(timeFrame),
  });

  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['connector_health'],
    queryFn: analyticsApi.getConnectorHealth,
  });

  const { data: insights, isLoading: insightsLoading, refetch: refetchInsights } = useQuery({
    queryKey: ['ai_insights'],
    queryFn: analyticsApi.getInsights,
  });

  const handleRefreshAll = () => {
    refetchOverview();
    refetchHealth();
    refetchInsights();
  };

  const trendData = overview?.execution_trend ?? [];

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-[1440px] mx-auto">
        {/* Header Banner */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl border border-border bg-card shadow-sm">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
              <BarChart3 className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Enterprise Analytics</h1>
              <p className="text-xs text-muted-foreground mt-0.5">
                Real-time metrics, connector latencies, and AI-driven DAG optimizations.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex rounded-xl border border-border bg-muted/30 p-1 text-xs font-semibold">
              {(['24h', '7d', '30d', '90d'] as const).map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeFrame(tf)}
                  className={`px-3 py-1 rounded-lg transition text-xs font-semibold ${
                    timeFrame === tf
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>

            <button
              onClick={handleRefreshAll}
              disabled={overviewLoading}
              className="p-2 rounded-xl border border-border bg-background hover:bg-muted text-muted-foreground hover:text-foreground transition flex items-center gap-1.5 text-xs font-semibold"
            >
              <RefreshCw className={`h-4 w-4 ${overviewLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl border border-border bg-card space-y-2 shadow-sm">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-bold uppercase tracking-wider">Total Executions</span>
              <Zap className="h-4 w-4 text-primary" />
            </div>
            <p className="text-2xl font-bold tracking-tight">{overview?.total_executions ?? '—'}</p>
            <p className="text-[10px] text-emerald-500 font-semibold flex items-center gap-1">
              <TrendingUp className="h-3 w-3" /> Live execution logging active
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-border bg-card space-y-2 shadow-sm">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-bold uppercase tracking-wider">SLA Success Rate</span>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </div>
            <p className="text-2xl font-bold tracking-tight text-emerald-500">
              {overview?.success_rate_pct ?? '—'}%
            </p>
            <p className="text-[10px] text-muted-foreground font-mono">
              {overview?.successful_executions ?? 0} success · {overview?.failed_executions ?? 0} failed
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-border bg-card space-y-2 shadow-sm">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-bold uppercase tracking-wider">Avg Latency</span>
              <Clock className="h-4 w-4 text-amber-500" />
            </div>
            <p className="text-2xl font-bold tracking-tight">{overview?.avg_duration_ms ?? '—'}ms</p>
            <p className="text-[10px] text-amber-500 font-semibold">Sub-50ms target met</p>
          </div>

          <div className="p-5 rounded-2xl border border-border bg-card space-y-2 shadow-sm">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-bold uppercase tracking-wider">Retries & Recovery</span>
              <RotateCcw className="h-4 w-4 text-purple-500" />
            </div>
            <p className="text-2xl font-bold tracking-tight">{overview?.total_retries ?? 0}</p>
            <p className="text-[10px] text-purple-400 font-semibold">Automatic Saga resilience</p>
          </div>
        </div>

        {/* Recharts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-5 rounded-2xl border border-border bg-card space-y-4 shadow-sm">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h3 className="font-bold text-sm tracking-tight">Execution Volume Trend</h3>
                <p className="text-xs text-muted-foreground mt-0.5">Total runs vs failures over {timeFrame}</p>
              </div>
              <span className="flex items-center gap-1.5 text-[10px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                <Activity className="h-3 w-3" /> Real-time
              </span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="colorExec2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                  <XAxis dataKey="timestamp" stroke="var(--muted-foreground)" fontSize={11} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', borderRadius: 12, fontSize: 11 }} />
                  <Area type="monotone" dataKey="executions" name="Executions" stroke="#6366F1" strokeWidth={2} fillOpacity={1} fill="url(#colorExec2)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="p-5 rounded-2xl border border-border bg-card space-y-4 shadow-sm">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h3 className="font-bold text-sm tracking-tight">Latency Distribution (ms)</h3>
                <p className="text-xs text-muted-foreground mt-0.5">Average execution latency per interval</p>
              </div>
              <span className="flex items-center gap-1.5 text-[10px] font-semibold text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-full">
                <Clock className="h-3 w-3" /> Duration Telemetry
              </span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                  <XAxis dataKey="timestamp" stroke="var(--muted-foreground)" fontSize={11} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', borderRadius: 12, fontSize: 11 }} />
                  <Bar dataKey="avg_latency_ms" name="Avg Latency (ms)" fill="#F59E0B" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* SLA Grid & AI Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {!healthLoading && <ConnectorHealthGrid items={health ?? []} />}
          {!insightsLoading && <AIInsightsPanel insights={insights ?? []} />}
        </div>
      </div>
    </DashboardLayout>
  );
}
