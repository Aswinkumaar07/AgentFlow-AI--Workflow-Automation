import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { analyticsApi } from '../api/analytics';
import { workflowApi } from '../api/workflows';
import { useAuthStore } from '../store/useAuthStore';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { DashboardCards } from '../components/dashboard/DashboardCards';
import { RecentWorkflowsTable } from '../components/dashboard/RecentWorkflowsTable';
import { Link } from 'react-router-dom';
import {
  Plus,
  RefreshCw,
  Sparkles,
  Activity,
  ShieldCheck,
  Zap,
  ArrowRight,
  Layers,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();

  const {
    data: overview,
    isLoading: analyticsLoading,
    refetch: refetchAnalytics,
  } = useQuery({
    queryKey: ['analytics_overview', '7d'],
    queryFn: () => analyticsApi.getOverview('7d'),
  });

  const {
    data: history,
    isLoading: historyLoading,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['history'],
    queryFn: workflowApi.getHistory,
  });

  const handleRefresh = () => {
    refetchAnalytics();
    refetchHistory();
  };

  const userName = user?.full_name?.split(' ')[0] || (user?.email ? user.email.split('@')[0] : 'Aswin');

  return (
    <DashboardLayout>
      <div className="max-w-[1400px] mx-auto space-y-8 font-sans">
        {/* ── 1. Page Header ───────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 sm:p-8 rounded-2xl bg-[#1B1728]/85 border border-[rgba(255,255,255,0.12)] shadow-2xl backdrop-blur-2xl relative overflow-hidden"
        >
          {/* Subtle Ambient Glow */}
          <div className="absolute top-0 right-1/4 w-96 h-96 bg-[radial-gradient(circle,rgba(255,109,0,0.12)_0%,transparent_70%)] pointer-events-none filter blur-3xl" />

          <div className="relative z-10">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Good morning, {userName} 👋
            </h1>
            <p className="text-xs sm:text-sm text-[rgba(255,255,255,0.60)] mt-2 font-medium">
              Here's what's happening across your workflows.
            </p>
          </div>

          <div className="flex items-center gap-3 relative z-10">
            <button
              onClick={handleRefresh}
              disabled={analyticsLoading || historyLoading}
              className="px-3.5 py-2.5 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#13102A] hover:bg-[#231E3A] hover:border-[#FF6D00]/40 text-[rgba(255,255,255,0.80)] transition-all text-xs font-bold flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 text-[#FF6D00] ${analyticsLoading || historyLoading ? 'animate-spin' : ''}`} />
              <span>Sync Telemetry</span>
            </button>
            <Link to="/builder">
              <button className="px-4 py-2.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] hover:brightness-110 text-white text-xs font-bold rounded-xl shadow-[0_4px_20px_rgba(255,109,0,0.35)] transition-all flex items-center gap-2">
                <Plus className="h-4 w-4" /> Create Workflow
              </button>
            </Link>
          </div>
        </motion.div>

        {/* ── 2. Overview KPI Cards ────────────────────────────────────── */}
        {analyticsLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 rounded-2xl bg-[#1B1728]/60 border border-[rgba(255,255,255,0.10)] animate-pulse" />
            ))}
          </div>
        ) : (
          <DashboardCards analytics={overview} />
        )}

        {/* ── 3. Quick Action / Build a Workflow Card ─────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.1, ease: 'easeOut' }}
          className="relative rounded-2xl bg-gradient-to-r from-[#1B1728]/90 via-[#231E3A]/85 to-[#13102A]/90 border border-[rgba(255,255,255,0.12)] p-6 sm:p-8 shadow-2xl backdrop-blur-2xl overflow-hidden group"
        >
          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-[radial-gradient(ellipse_at_top_right,rgba(255,109,0,0.16),transparent_70%)] pointer-events-none" />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-[#FF6D00]/15 border border-[#FF6D00]/30 text-[#FF6D00] text-[11px] font-bold uppercase tracking-wider mb-1">
                <Zap className="h-3.5 w-3.5 fill-current" /> AI Workflow Engine
              </div>
              <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                Build a workflow
              </h2>
              <p className="text-xs sm:text-sm text-[rgba(255,255,255,0.65)] font-medium leading-relaxed">
                Turn a natural-language task into an executable workflow.
              </p>
            </div>

            {/* DAG Diagram Visual Decoration */}
            <div className="hidden md:flex items-center gap-3 px-4 py-3 rounded-xl bg-[rgba(0,0,0,0.25)] border border-[rgba(255,255,255,0.10)] font-mono text-[11px] text-[rgba(255,255,255,0.70)]">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#FF6D00]/20 border border-[#FF6D00]/40 text-[#FF6D00] font-bold">
                <Zap className="h-3.5 w-3.5" /> Prompt
              </div>
              <div className="h-0.5 w-6 bg-gradient-to-r from-[#FF6D00] to-[#06B6D4]" />
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#06B6D4]/20 border border-[#06B6D4]/40 text-[#06B6D4] font-bold">
                <Layers className="h-3.5 w-3.5" /> DAG Plan
              </div>
              <div className="h-0.5 w-6 bg-gradient-to-r from-[#06B6D4] to-[#22C55E]" />
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#22C55E]/20 border border-[#22C55E]/40 text-[#34D399] font-bold">
                <Sparkles className="h-3.5 w-3.5" /> Execute
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Link to="/builder">
                <button className="px-5 py-3 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] hover:brightness-110 text-white font-bold text-xs rounded-xl shadow-[0_4px_20px_rgba(255,109,0,0.35)] transition-all flex items-center gap-2">
                  <span>Create Workflow</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              </Link>
              <Link to="/templates">
                <button className="px-4 py-3 bg-[#13102A] hover:bg-[#231E3A] border border-[rgba(255,255,255,0.12)] text-[rgba(255,255,255,0.80)] font-bold text-xs rounded-xl transition-all">
                  Browse Templates
                </button>
              </Link>
            </div>
          </div>
        </motion.div>

        {/* ── 4. Connector & System Health Grid Banner ─────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.15, ease: 'easeOut' }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <div className="p-5 rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728]/85 backdrop-blur-2xl flex items-center gap-4 shadow-xl hover:border-[#22C55E]/40 transition-all group">
            <div className="h-11 w-11 rounded-xl bg-[#22C55E]/15 border border-[#22C55E]/30 text-[#34D399] flex items-center justify-center font-bold shadow-[0_0_15px_rgba(34,197,94,0.15)] group-hover:scale-105 transition-transform">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">LLM Resilience Layer</h4>
              <p className="text-[11px] text-[rgba(255,255,255,0.55)] mt-0.5 font-medium">Provider Strategy & Circuit Breaker Active</p>
            </div>
          </div>

          <div className="p-5 rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728]/85 backdrop-blur-2xl flex items-center gap-4 shadow-xl hover:border-[#06B6D4]/40 transition-all group">
            <div className="h-11 w-11 rounded-xl bg-[#06B6D4]/15 border border-[#06B6D4]/30 text-[#38BDF8] flex items-center justify-center font-bold shadow-[0_0_15px_rgba(6,182,212,0.15)] group-hover:scale-105 transition-transform">
              <Activity className="h-6 w-6" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">API Intelligence Platform</h4>
              <p className="text-[11px] text-[rgba(255,255,255,0.55)] mt-0.5 font-medium">Sub-50ms Hybrid Vector Search</p>
            </div>
          </div>

          <div className="p-5 rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728]/85 backdrop-blur-2xl flex items-center gap-4 shadow-xl hover:border-[#A855F7]/40 transition-all group">
            <div className="h-11 w-11 rounded-xl bg-[#A855F7]/15 border border-[#A855F7]/30 text-[#C084FC] flex items-center justify-center font-bold shadow-[0_0_15px_rgba(168,85,247,0.15)] group-hover:scale-105 transition-transform">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">Connector Framework</h4>
              <p className="text-[11px] text-[rgba(255,255,255,0.55)] mt-0.5 font-medium">HTTP/2 Pool & AES-256 Secret Vault</p>
            </div>
          </div>
        </motion.div>

        {/* ── 5. Recent Workflows Section ─────────────────────────────── */}
        {historyLoading ? (
          <div className="h-64 rounded-2xl bg-[#1B1728]/60 border border-[rgba(255,255,255,0.10)] animate-pulse" />
        ) : (
          <RecentWorkflowsTable items={history} />
        )}
      </div>
    </DashboardLayout>
  );
};

