import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { ConnectorHealthGrid } from '../components/analytics/ConnectorHealthGrid';
import { AIInsightsPanel } from '../components/analytics/AIInsightsPanel';
import {
  BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  BarChart3, RefreshCw, Zap, CheckCircle2, Clock, RotateCcw, TrendingUp
} from 'lucide-react';

const dateRanges = [
  { id: '24h', label: '24 Hours' },
  { id: '7d', label: '7 Days' },
  { id: '30d', label: '30 Days' },
  { id: '90d', label: '90 Days' },
] as const;

export const AnalyticsPage: React.FC = () => {
  const [timeFrame, setTimeFrame] = useState<'24h' | '7d' | '30d' | '90d'>('7d');

  const {
    data: overview,
    isLoading: overviewLoading,
    refetch: refetchOverview,
  } = useQuery({
    queryKey: ['analytics_overview', timeFrame],
    queryFn: () => analyticsApi.getOverview(timeFrame),
  });

  const { data: health, refetch: refetchHealth } = useQuery({
    queryKey: ['connector_health'],
    queryFn: analyticsApi.getConnectorHealth,
  });

  const { data: insights, refetch: refetchInsights } = useQuery({
    queryKey: ['ai_insights'],
    queryFn: analyticsApi.getInsights,
  });

  const handleRefreshAll = () => {
    refetchOverview();
    refetchHealth();
    refetchInsights();
  };

  const trendData = (overview?.execution_trend ?? []).map((item) => ({
    ...item,
    success: Math.max(0, item.executions - item.failures),
  }));

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-[1440px] mx-auto">

        {/* ── 1. Header Banner ── */}
        <div className="p-6 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md shadow-[0_8px_32px_rgba(0,0,0,0.36)] flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-[#FF6D00]/10 to-[#FF0C00]/5 blur-3xl pointer-events-none rounded-full" />

          <div className="flex items-center gap-4 relative z-10">
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] flex items-center justify-center text-white shadow-[0_4px_20px_rgba(255,109,0,0.4)] shrink-0">
              <BarChart3 className="h-7 w-7" />
            </div>

            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-extrabold text-white tracking-tight">Enterprise Telemetry & Analytics</h1>
                <span className="px-2.5 py-0.5 rounded-full bg-[#22C55E]/15 border border-[#22C55E]/30 text-[#22C55E] text-[10px] font-bold uppercase tracking-wider">
                  Real-time Telemetry
                </span>
              </div>
              <p className="text-xs text-[rgba(255,255,255,0.6)] mt-1">
                Real-time workflow execution metrics, connector health, and AI-driven optimization insights.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 relative z-10 self-start md:self-auto flex-wrap">
            {/* Timeframe Filter Pills */}
            <div className="flex rounded-xl border border-[rgba(255,255,255,0.1)] bg-[#1B1728] p-1 text-xs font-semibold">
              {dateRanges.map((tf) => (
                <button
                  key={tf.id}
                  onClick={() => setTimeFrame(tf.id as any)}
                  className={`px-3 py-1.5 rounded-lg transition text-xs font-semibold ${
                    timeFrame === tf.id
                      ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-sm font-bold'
                      : 'text-[rgba(255,255,255,0.6)] hover:text-white'
                  }`}
                >
                  {tf.label}
                </button>
              ))}
            </div>

            <button
              onClick={handleRefreshAll}
              disabled={overviewLoading}
              className="p-2.5 rounded-xl border border-[rgba(255,255,255,0.15)] bg-[#1B1728] hover:bg-[#231E3A] hover:border-[#FF6D00]/50 text-xs font-bold text-white transition shadow-md disabled:opacity-50"
              title="Refresh Telemetry"
            >
              <RefreshCw className={`h-4 w-4 text-[#FF6D00] ${overviewLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* ── 2. KPI Metrics Cards ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md space-y-2 shadow-sm hover:border-[rgba(255,255,255,0.22)] hover:bg-[#1B1728]/90 transition duration-200">
            <div className="flex items-center justify-between text-[rgba(255,255,255,0.5)]">
              <span className="text-[10px] font-bold uppercase tracking-wider">Total Executions</span>
              <Zap className="h-4 w-4 text-[#FF6D00]" />
            </div>
            <p className="text-2xl font-extrabold text-white tracking-tight">{overview?.total_executions ?? '—'}</p>
            <p className="text-[10px] text-[#22C55E] font-semibold flex items-center gap-1">
              <TrendingUp className="h-3 w-3" /> Live execution telemetry active
            </p>
          </div>

          <div className="p-5 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md space-y-2 shadow-sm hover:border-[rgba(255,255,255,0.22)] hover:bg-[#1B1728]/90 transition duration-200">
            <div className="flex items-center justify-between text-[rgba(255,255,255,0.5)]">
              <span className="text-[10px] font-bold uppercase tracking-wider">Success Rate</span>
              <CheckCircle2 className="h-4 w-4 text-[#22C55E]" />
            </div>
            <p className="text-2xl font-extrabold tracking-tight text-[#22C55E]">
              {overview?.success_rate_pct ?? '—'}%
            </p>
            <p className="text-[10px] text-[rgba(255,255,255,0.5)] font-mono">
              {overview?.successful_executions ?? 0} success · {overview?.failed_executions ?? 0} failed
            </p>
          </div>

          <div className="p-5 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md space-y-2 shadow-sm hover:border-[rgba(255,255,255,0.22)] hover:bg-[#1B1728]/90 transition duration-200">
            <div className="flex items-center justify-between text-[rgba(255,255,255,0.5)]">
              <span className="text-[10px] font-bold uppercase tracking-wider">Average Duration</span>
              <Clock className="h-4 w-4 text-[#F59E0B]" />
            </div>
            <p className="text-2xl font-extrabold text-white tracking-tight">{overview?.avg_duration_ms ?? '—'}ms</p>
            <p className="text-[10px] text-[rgba(255,255,255,0.5)] font-semibold">Average execution duration</p>
          </div>

          <div className="p-5 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md space-y-2 shadow-sm hover:border-[rgba(255,255,255,0.22)] hover:bg-[#1B1728]/90 transition duration-200">
            <div className="flex items-center justify-between text-[rgba(255,255,255,0.5)]">
              <span className="text-[10px] font-bold uppercase tracking-wider">Retries & Recovery</span>
              <RotateCcw className="h-4 w-4 text-purple-400" />
            </div>
            <p className="text-2xl font-extrabold text-white tracking-tight">{overview?.total_retries ?? 0}</p>
            <p className="text-[10px] text-purple-400 font-semibold">Automatic Saga resilience</p>
          </div>
        </div>

        {/* ── 3. Recharts Execution Telemetry Trends Grid ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Execution Volume Trend Area Chart */}
          <div className="p-6 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md space-y-4 shadow-sm">
            <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.08)] pb-3">
              <div>
                <h3 className="font-bold text-sm text-white tracking-tight">Execution Volume Trend</h3>
                <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5">Execution throughput over {timeFrame}</p>
              </div>
              <span className="text-[10px] font-mono font-bold text-[#FF6D00] bg-[#FF6D00]/10 px-2.5 py-1 rounded-lg border border-[#FF6D00]/20">
                {trendData.length} Data Points
              </span>
            </div>

            <div className="h-64 w-full">
              {trendData.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-[rgba(255,255,255,0.4)]">
                  No telemetry volume data available.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trendData}>
                    <defs>
                      <linearGradient id="execVolumeGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#FF6D00" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#FF6D00" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="timestamp" stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} />
                    <YAxis stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1B1728',
                        borderColor: 'rgba(255,255,255,0.15)',
                        borderRadius: '12px',
                        color: '#fff',
                        fontSize: '12px',
                      }}
                    />
                    <Area type="monotone" dataKey="executions" stroke="#FF6D00" strokeWidth={2.5} fillOpacity={1} fill="url(#execVolumeGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Success vs Failure Bar Chart */}
          <div className="p-6 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md space-y-4 shadow-sm">
            <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.08)] pb-3">
              <div>
                <h3 className="font-bold text-sm text-white tracking-tight">Success vs Failure Breakdown</h3>
                <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5">Execution outcome classification</p>
              </div>
              <span className="text-[10px] font-mono font-bold text-[#22C55E] bg-[#22C55E]/10 px-2.5 py-1 rounded-lg border border-[#22C55E]/20">
                Execution Outcomes
              </span>
            </div>

            <div className="h-64 w-full">
              {trendData.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-[rgba(255,255,255,0.4)]">
                  No outcome classification data available.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="timestamp" stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} />
                    <YAxis stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1B1728',
                        borderColor: 'rgba(255,255,255,0.15)',
                        borderRadius: '12px',
                        color: '#fff',
                        fontSize: '12px',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                    <Bar dataKey="success" name="Successful" fill="#22C55E" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="failures" name="Failed" fill="#EF4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        {/* ── 4. SaaS Connector SLA & Health Grid ── */}
        <ConnectorHealthGrid items={health} />

        {/* ── 5. AI Telemetry Optimization Insights Panel ── */}
        <AIInsightsPanel insights={insights} />
      </div>
    </DashboardLayout>
  );
};
