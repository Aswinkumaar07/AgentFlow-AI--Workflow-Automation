import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { workflowApi } from '../api/workflows';
import type { WorkflowItem } from '../types/workflow';
import { VersionHistoryModal } from '../components/builder/VersionHistoryModal';
import { ExecutionHistoryModal } from '../components/builder/ExecutionHistoryModal';
import { SchedulesTriggersModal } from '../components/builder/SchedulesTriggersModal';
import { useWorkflowStore } from '../store/useWorkflowStore';
import {
  Workflow,
  Plus,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  Play,
  RotateCw,
  LayoutGrid,
  List,
  ArrowUpDown,
  History,
  PlayCircle,
  ChevronRight,
  Filter,
  Layers,
} from 'lucide-react';

const getWorkflowProvider = (item: WorkflowItem): string => {
  if (item.definition && Array.isArray(item.definition.nodes)) {
    const providers = Array.from(
      new Set(
        item.definition.nodes
          .map((n) => n.provider || n.type)
          .filter((p): p is string => Boolean(p))
      )
    );
    if (providers.length > 0) return providers.join(', ');
  }
  return item.trigger_type ? item.trigger_type.toUpperCase() : 'GENERIC';
};

export const WorkflowsPage: React.FC = () => {
  const navigate = useNavigate();

  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedProvider, setSelectedProvider] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'name'>('newest');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  // Modal triggers
  const [activeModal, setActiveModal] = useState<{
    type: 'version' | 'execution' | 'schedule' | null;
    workflowId?: string;
  }>({ type: null });

  // Load persistent workflow entities from backend API
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<{ items: WorkflowItem[]; total: number }>({
    queryKey: ['workflows_list'],
    queryFn: workflowApi.getWorkflows,
    refetchInterval: 15000,
  });

  React.useEffect(() => {
    const handleWorkflowCreated = () => {
      refetch();
    };
    window.addEventListener('workflow-created', handleWorkflowCreated);
    return () => {
      window.removeEventListener('workflow-created', handleWorkflowCreated);
    };
  }, [refetch]);

  const workflows = data?.items || [];
  const totalCount = data?.total ?? workflows.length;

  // Extract unique providers/connectors for filter dropdown
  const uniqueProviders = useMemo(() => {
    const set = new Set<string>();
    workflows.forEach((item) => {
      const p = getWorkflowProvider(item);
      if (p) set.add(p);
    });
    return Array.from(set);
  }, [workflows]);

  // Filter & Sort actual workflow records
  const filteredWorkflows = useMemo(() => {
    let result = [...workflows];

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (w) =>
          (w.title && w.title.toLowerCase().includes(q)) ||
          (w.id && w.id.toLowerCase().includes(q)) ||
          getWorkflowProvider(w).toLowerCase().includes(q)
      );
    }

    if (selectedStatus !== 'ALL') {
      result = result.filter(
        (w) => (w.status || 'ACTIVE').toUpperCase() === selectedStatus.toUpperCase()
      );
    }

    if (selectedProvider !== 'ALL') {
      result = result.filter((w) => getWorkflowProvider(w) === selectedProvider);
    }

    result.sort((a, b) => {
      if (sortBy === 'name') return (a.title || '').localeCompare(b.title || '');
      const timeA = new Date(a.updated_at || a.created_at || 0).getTime() || 0;
      const timeB = new Date(b.updated_at || b.created_at || 0).getTime() || 0;
      if (sortBy === 'oldest') return timeA - timeB;
      return timeB - timeA; // newest first
    });

    return result;
  }, [workflows, search, selectedStatus, selectedProvider, sortBy]);

  const handleOpenBuilder = (item?: WorkflowItem) => {
    if (item) {
      useWorkflowStore.getState().loadWorkflowFromDefinition(item);
      const targetId = item.definition?.workflow_id || item.id;
      navigate(`/builder?id=${encodeURIComponent(targetId)}`);
    } else {
      navigate('/builder');
    }
  };

  const statusBadge = (status: string) => {
    const upper = (status || 'ACTIVE').toUpperCase();
    switch (upper) {
      case 'ACTIVE':
      case 'PUBLISHED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#22C55E]/15 text-[#34D399] border border-[#22C55E]/30 shadow-[0_0_10px_rgba(34,197,94,0.15)]">
            <CheckCircle2 className="h-3 w-3" /> ACTIVE
          </span>
        );
      case 'DRAFT':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#06B6D4]/15 text-[#38BDF8] border border-[#06B6D4]/30 shadow-[0_0_10px_rgba(6,182,212,0.15)]">
            <Clock className="h-3 w-3" /> DRAFT
          </span>
        );
      case 'PAUSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30 shadow-[0_0_10px_rgba(255,109,0,0.15)]">
            <Clock className="h-3 w-3" /> PAUSED
          </span>
        );
      case 'ARCHIVED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-white/10 text-white/60 border border-white/20">
            <AlertCircle className="h-3 w-3" /> ARCHIVED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-white/10 text-white/70 border border-white/20">
            {upper}
          </span>
        );
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-[1440px] mx-auto pb-12">
        {/* ── 1. WORKFLOWS PAGE HEADER ─────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.12)] shadow-xl">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center font-bold shadow-[0_0_15px_rgba(255,109,0,0.20)]">
              <Workflow className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl font-bold tracking-tight text-white">Workflows</h1>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30">
                  {totalCount} Total
                </span>
              </div>
              <p className="text-xs text-[#A098AE] mt-1 font-medium">
                Build, manage, and monitor your automation workflows.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => refetch()}
              disabled={isLoading}
              className="px-3.5 py-2.5 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-xs font-semibold text-[#A098AE] hover:text-white transition flex items-center gap-2 cursor-pointer"
              title="Refresh Workflows List"
            >
              <RotateCw className={`h-3.5 w-3.5 text-[#FF6D00] ${isLoading ? 'animate-spin' : ''}`} />
              <span>Sync</span>
            </button>
            <button
              onClick={() => handleOpenBuilder()}
              className="px-5 py-2.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl hover:opacity-95 transition flex items-center gap-2 shadow-[0_0_20px_rgba(255,109,0,0.35)] cursor-pointer"
            >
              <Plus className="h-4 w-4 stroke-[3]" />
              <span>Create Workflow</span>
            </button>
          </div>
        </div>

        {/* ── 2. SEARCH + FILTER BAR ────────────────────────────────────── */}
        <div className="p-4 rounded-2xl bg-[#13102A]/70 backdrop-blur-xl border border-[rgba(255,255,255,0.10)] flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between shadow-lg">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#7A748E]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search workflows by name, ID, or provider..."
              className="w-full pl-10 pr-4 py-2 text-xs bg-[#0E0918] text-white placeholder-[#7A748E] rounded-xl border border-[rgba(255,255,255,0.12)] focus:outline-none focus:border-[#FF6D00] focus:ring-1 focus:ring-[#FF6D00] transition shadow-inner font-sans"
            />
          </div>

          {/* Filters & View Controls */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Status Filter */}
            <div className="flex items-center gap-1.5 bg-[#0E0918] border border-[rgba(255,255,255,0.12)] rounded-xl px-2.5 py-1.5 text-xs">
              <Filter className="h-3.5 w-3.5 text-[#FF6D00]" />
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
              >
                <option value="ALL" className="bg-[#13102A] text-white">All Statuses</option>
                <option value="ACTIVE" className="bg-[#13102A] text-white">Active</option>
                <option value="DRAFT" className="bg-[#13102A] text-white">Draft</option>
                <option value="PAUSED" className="bg-[#13102A] text-white">Paused</option>
                <option value="ARCHIVED" className="bg-[#13102A] text-white">Archived</option>
              </select>
            </div>

            {/* Provider Filter */}
            {uniqueProviders.length > 0 && (
              <div className="flex items-center gap-1.5 bg-[#0E0918] border border-[rgba(255,255,255,0.12)] rounded-xl px-2.5 py-1.5 text-xs">
                <Layers className="h-3.5 w-3.5 text-[#FF6D00]" />
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
                >
                  <option value="ALL" className="bg-[#13102A] text-white">All Providers</option>
                  {uniqueProviders.map((p) => (
                    <option key={p} value={p} className="bg-[#13102A] text-white">
                      {p}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Sort Dropdown */}
            <div className="flex items-center gap-1.5 bg-[#0E0918] border border-[rgba(255,255,255,0.12)] rounded-xl px-2.5 py-1.5 text-xs">
              <ArrowUpDown className="h-3.5 w-3.5 text-[#A098AE]" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
              >
                <option value="newest" className="bg-[#13102A] text-white">Newest First</option>
                <option value="oldest" className="bg-[#13102A] text-white">Oldest First</option>
                <option value="name" className="bg-[#13102A] text-white">Name A–Z</option>
              </select>
            </div>

            {/* View Mode Toggle */}
            <div className="flex rounded-xl bg-[#0E0918] p-1 border border-[rgba(255,255,255,0.12)] text-xs">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-lg transition cursor-pointer ${
                  viewMode === 'grid'
                    ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-[0_0_10px_rgba(255,109,0,0.30)]'
                    : 'text-[#A098AE] hover:text-white'
                }`}
                title="Grid View"
              >
                <LayoutGrid className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`p-1.5 rounded-lg transition cursor-pointer ${
                  viewMode === 'table'
                    ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-[0_0_10px_rgba(255,109,0,0.30)]'
                    : 'text-[#A098AE] hover:text-white'
                }`}
                title="Table View"
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* ── 3. LOADING STATE (SKELETON) ────────────────────────────────── */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((idx) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] space-y-4 animate-pulse"
              >
                <div className="flex items-center justify-between">
                  <div className="h-10 w-10 rounded-xl bg-[#1B1728]" />
                  <div className="h-5 w-20 rounded-full bg-[#1B1728]" />
                </div>
                <div className="space-y-2">
                  <div className="h-4 w-3/4 rounded bg-[#1B1728]" />
                  <div className="h-3 w-1/2 rounded bg-[#1B1728]" />
                </div>
                <div className="pt-3 border-t border-[rgba(255,255,255,0.06)] flex justify-between">
                  <div className="h-3 w-20 rounded bg-[#1B1728]" />
                  <div className="h-3 w-16 rounded bg-[#1B1728]" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── 4. ERROR STATE ────────────────────────────────────────────── */}
        {isError && !isLoading && (
          <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 flex flex-col items-center justify-center text-center space-y-3">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <div>
              <h3 className="text-sm font-bold text-white">Failed to load workflows</h3>
              <p className="text-xs text-red-300 mt-1 font-mono">
                {error instanceof Error ? error.message : 'Backend request failed.'}
              </p>
            </div>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 text-xs font-bold rounded-xl transition flex items-center gap-1.5 cursor-pointer"
            >
              <RotateCw className="h-3.5 w-3.5" /> Retry Load
            </button>
          </div>
        )}

        {/* ── 5. EMPTY STATE ────────────────────────────────────────────── */}
        {!isLoading && !isError && filteredWorkflows.length === 0 && (
          <div className="p-12 text-center rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.12)] shadow-xl max-w-lg mx-auto space-y-4 my-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center mx-auto shadow-[0_0_20px_rgba(255,109,0,0.20)]">
              <Workflow className="h-8 w-8" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Create your first workflow</h3>
              <p className="text-xs text-[#A098AE] mt-1 leading-relaxed">
                Turn a natural-language task into an executable automation.
              </p>
            </div>
            <button
              onClick={() => handleOpenBuilder()}
              className="px-5 py-2.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl hover:opacity-95 transition inline-flex items-center gap-2 shadow-[0_0_20px_rgba(255,109,0,0.35)] cursor-pointer"
            >
              <Plus className="h-4 w-4 stroke-[3]" /> Create Workflow
            </button>
          </div>
        )}

        {/* ── 6. WORKFLOW LIST (GRID OR TABLE) ───────────────────────────── */}
        {!isLoading && !isError && filteredWorkflows.length > 0 && (
          <AnimatePresence mode="wait">
            {viewMode === 'grid' ? (
              <motion.div
                key="grid-view"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
              >
                {filteredWorkflows.map((item) => (
                  <div
                    key={item.id}
                    className="group rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.12)] p-5 shadow-xl hover:border-[#FF6D00]/40 hover:shadow-[0_0_20px_rgba(255,109,0,0.18)] transition-all duration-200 flex flex-col justify-between space-y-4"
                  >
                    <div>
                      {/* Top Header */}
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="h-10 w-10 rounded-xl bg-[#FF6D00]/10 border border-[#FF6D00]/25 text-[#FF6D00] flex items-center justify-center font-bold shrink-0">
                          <Workflow className="h-5 w-5" />
                        </div>
                        {statusBadge(item.status)}
                      </div>

                      {/* Title & Primary Workflow ID */}
                      <div className="space-y-1">
                        <h3 className="font-bold text-sm text-white group-hover:text-[#FF6D00] transition line-clamp-1">
                          {item.title || `Workflow ${item.id}`}
                        </h3>
                        <p className="text-[10px] font-mono text-[#A098AE] truncate">
                          ID: <span className="text-[#FF6D00]">{item.id}</span>
                        </p>
                      </div>
                    </div>

                    {/* Stats & Connector Badge */}
                    <div className="space-y-2 pt-3 border-t border-[rgba(255,255,255,0.08)]">
                      <div className="flex items-center justify-between text-[11px] text-[#A098AE]">
                        <span className="flex items-center gap-1 font-mono">
                          <Layers className="h-3 w-3 text-[#FF6D00]" /> {getWorkflowProvider(item)}
                        </span>
                        <span className="font-mono text-[10px] bg-[#1B1728] px-2 py-0.5 rounded border border-[rgba(255,255,255,0.08)]">
                          v{item.version || 1}
                        </span>
                      </div>

                      <div className="text-[10px] text-[#7A748E] flex items-center justify-between font-mono">
                        <span>
                          {item.created_at
                            ? `Created: ${new Date(item.created_at).toLocaleDateString()}`
                            : 'Recent'}
                        </span>
                        <span className="bg-[#1B1728] px-1.5 py-0.5 rounded border border-[rgba(255,255,255,0.08)]">
                          {item.trigger_type || 'manual'}
                        </span>
                      </div>
                    </div>

                    {/* Action Bar */}
                    <div className="pt-2 flex items-center justify-between gap-1.5">
                      <button
                        onClick={() => handleOpenBuilder(item)}
                        className="flex-1 py-2 px-3 rounded-xl bg-[#1B1728] hover:bg-[#231E3A] border border-[rgba(255,255,255,0.10)] hover:border-[#FF6D00]/30 text-xs font-bold text-white transition flex items-center justify-center gap-1.5 cursor-pointer"
                      >
                        <Play className="h-3 w-3 text-[#FF6D00] fill-current" /> Open Studio
                      </button>

                      <button
                        onClick={() => setActiveModal({ type: 'version', workflowId: item.definition?.workflow_id || item.id })}
                        className="p-2 rounded-xl bg-[#1B1728] hover:bg-[#231E3A] border border-[rgba(255,255,255,0.10)] text-[#A098AE] hover:text-white transition cursor-pointer"
                        title="Version History"
                      >
                        <History className="h-3.5 w-3.5" />
                      </button>

                      <button
                        onClick={() => setActiveModal({ type: 'execution', workflowId: item.id })}
                        className="p-2 rounded-xl bg-[#1B1728] hover:bg-[#231E3A] border border-[rgba(255,255,255,0.10)] text-[#A098AE] hover:text-white transition cursor-pointer"
                        title="Execution History"
                      >
                        <PlayCircle className="h-3.5 w-3.5" />
                      </button>

                      <button
                        onClick={() => setActiveModal({ type: 'schedule', workflowId: item.id })}
                        className="p-2 rounded-xl bg-[#1B1728] hover:bg-[#231E3A] border border-[rgba(255,255,255,0.10)] text-[#A098AE] hover:text-white transition cursor-pointer"
                        title="Schedules & Triggers"
                      >
                        <Clock className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </motion.div>
            ) : (
              <motion.div
                key="table-view"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728]/85 overflow-hidden shadow-2xl backdrop-blur-2xl"
              >
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#13102A]/80 text-[#A098AE] font-bold border-b border-[rgba(255,255,255,0.08)] uppercase tracking-wider">
                      <tr>
                        <th className="py-3.5 px-6">Workflow Name</th>
                        <th className="py-3.5 px-6">Provider / Trigger</th>
                        <th className="py-3.5 px-6">Status</th>
                        <th className="py-3.5 px-6">Version</th>
                        <th className="py-3.5 px-6">Created Date</th>
                        <th className="py-3.5 px-6 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[rgba(255,255,255,0.06)]">
                      {filteredWorkflows.map((item) => (
                        <tr key={item.id} className="hover:bg-[#231E3A]/40 transition">
                          <td className="py-4 px-6 font-bold text-white">
                            <div className="flex items-center gap-2.5">
                              <div className="h-7 w-7 rounded-lg bg-[#FF6D00]/10 border border-[#FF6D00]/20 text-[#FF6D00] flex items-center justify-center font-bold shrink-0">
                                <Workflow className="h-3.5 w-3.5" />
                              </div>
                              <div>
                                <span>{item.title || `Workflow ${item.id}`}</span>
                                <span className="block text-[10px] font-mono text-[#7A748E] font-normal">
                                  ID: {item.id}
                                </span>
                              </div>
                            </div>
                          </td>
                          <td className="py-4 px-6 font-mono text-[11px] text-[#A098AE]">
                            <span className="px-2 py-0.5 rounded-md bg-[#13102A] border border-[rgba(255,255,255,0.10)] text-white">
                              {getWorkflowProvider(item)}
                            </span>
                          </td>
                          <td className="py-4 px-6">{statusBadge(item.status)}</td>
                          <td className="py-4 px-6 font-mono text-[11px] text-[#A098AE]">
                            v{item.version || 1}
                          </td>
                          <td className="py-4 px-6 text-[#A098AE] font-mono text-[11px]">
                            {item.created_at
                              ? new Date(item.created_at).toLocaleDateString()
                              : 'Recent'}
                          </td>
                          <td className="py-4 px-6 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                onClick={() => handleOpenBuilder(item)}
                                className="px-3 py-1.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-[11px] font-bold rounded-lg hover:opacity-90 transition flex items-center gap-1 shadow-sm cursor-pointer"
                              >
                                Edit <ChevronRight className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>

      {/* ── MODALS INTEGRATION ─────────────────────────────────────────── */}
      <VersionHistoryModal
        isOpen={activeModal.type === 'version'}
        workflowId={activeModal.workflowId}
        onClose={() => setActiveModal({ type: null })}
      />
      <ExecutionHistoryModal
        isOpen={activeModal.type === 'execution'}
        onClose={() => setActiveModal({ type: null })}
        onSelectExecution={() => {}}
      />
      <SchedulesTriggersModal
        isOpen={activeModal.type === 'schedule'}
        onClose={() => setActiveModal({ type: null })}
      />
    </DashboardLayout>
  );
};
