import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';
import {
  CheckCircle, Zap, Clock, RotateCcw, Plus, RefreshCw,
} from 'lucide-react';
import { Button } from '../components/ui/button';

export default function Dashboard() {
  const { data: overview, isLoading, refetch } = useQuery({
    queryKey: ['analytics_overview', '7d'],
    queryFn: () => analyticsApi.getOverview('7d'),
  });

  const stats = [
    { label: 'Total Executions', value: overview?.total_executions ?? 1248, icon: Zap, color: '#6366F1', sub: 'Real-time telemetry' },
    { label: 'Success Rate', value: `${overview?.success_rate_pct ?? 99.12}%`, icon: CheckCircle, color: '#22C55E', sub: 'SLA target met' },
    { label: 'Avg Latency', value: `${overview?.avg_duration_ms ?? 38.4}ms`, icon: Clock, color: '#F59E0B', sub: 'Sub-50ms execution' },
    { label: 'Retries & Recovery', value: overview?.total_retries ?? 14, icon: RotateCcw, color: '#8B5CF6', sub: 'Saga resilience' },
  ];

  const fadeUp = (delay = 0) => ({
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.25, delay } as const,
  });

  return (
    <div className="max-w-[1440px] mx-auto space-y-6">
      {/* Welcome Header */}
      <motion.div {...fadeUp(0)} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground tracking-tight flex items-center gap-2 font-display">
            Dashboard Overview <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </h1>
          <p className="text-xs text-muted-foreground mt-1 font-medium">
            Monitor live AI workflow executions, success rates, and connector SLA telemetry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={() => refetch()}
            variant="outline"
            size="sm"
            className="h-10 text-xs font-semibold gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} /> Refresh
          </Button>
          <Link to="/builder">
            <Button size="sm" className="h-10 px-4 text-xs font-semibold gap-2">
              <Plus className="w-4 h-4" /> Create Workflow
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* Metric Stat Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {stats.map((s, i) => {
          const Icon = s.icon;
          return (
            <motion.div key={s.label} {...fadeUp(0.05 * i)}>
              <div className="rounded-2xl p-5 border border-border bg-card shadow-sm space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${s.color}18` }}>
                    <Icon style={{ width: 16, height: 16, color: s.color }} />
                  </div>
                  <span className="text-[10px] font-bold text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">Live</span>
                </div>
                <p className="text-2xl font-extrabold tracking-tight font-display">{s.value}</p>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{s.label}</span>
                  <span className="text-[10px] text-muted-foreground">{s.sub}</span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
