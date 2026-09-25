import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  PauseCircle,
  RefreshCw,
  Search,
  Eye,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  X,
  Loader2,
  Check,
} from 'lucide-react';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { workflowApi } from '../api/workflows';
import { ExecutionResultInspector } from '../components/builder/ExecutionResultInspector';
import type { WorkflowHistoryItem } from '../types/workflow';

type NormalizedStatus = 'success' | 'error' | 'running' | 'pending' | 'cancelled';

const statusConfig: Record<
  NormalizedStatus,
  { label: string; bg: string; border: string; text: string; dot: string; icon: React.FC<React.SVGProps<SVGSVGElement>> }
> = {
  success: {
    label: 'COMPLETED',
    bg: 'bg-[#22C55E]/15',
    border: 'border-[#22C55E]/30',
    text: 'text-[#34D399]',
    dot: '#22C55E',
    icon: CheckCircle2,
  },
  error: {
    label: 'FAILED',
    bg: 'bg-red-500/15',
    border: 'border-red-500/30',
    text: 'text-red-400',
    dot: '#EF4444',
    icon: XCircle,
  },
  running: {
    label: 'RUNNING',
    bg: 'bg-cyan-500/15',
    border: 'border-cyan-500/30',
    text: 'text-cyan-300',
    dot: '#06B6D4',
    icon: RefreshCw,
  },
  pending: {
    label: 'WAITING',
    bg: 'bg-amber-500/15',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    dot: '#F59E0B',
    icon: PauseCircle,
  },
  cancelled: {
    label: 'CANCELLED',
    bg: 'bg-white/10',
    border: 'border-white/20',
    text: 'text-white/60',
    dot: '#71717A',
    icon: AlertCircle,
  },
};

export const normalizeStatus = (statusRaw?: string): NormalizedStatus => {
  const s = (statusRaw || '').toLowerCase();
  if (s === 'completed' || s === 'success') return 'success';
  if (
    s === 'failed' ||
    s === 'error' ||
    s === 'blocked_missing_connection' ||
    s === 'blocked' ||
    s === 'missing_connection'
  ) return 'error';
  if (s === 'running') return 'running';
  if (s === 'waiting' || s === 'waiting_for_approval' || s === 'paused' || s === 'pending') return 'pending';
  if (s === 'cancelled') return 'cancelled';
  return 'error';
};

export const formatReplayNotificationMessage = (execId: string, rawStatus?: string): string => {
  const s = (rawStatus || '').toUpperCase();
  let displayStatus = rawStatus || 'COMPLETED';

  if (s === 'COMPLETED' || s === 'SUCCESS') {
    displayStatus = 'COMPLETED';
  } else if (s === 'FAILED' || s === 'ERROR') {
    displayStatus = 'FAILED';
  } else if (s === 'BLOCKED_MISSING_CONNECTION' || s === 'BLOCKED' || s === 'MISSING_CONNECTION') {
    displayStatus = 'BLOCKED_MISSING_CONNECTION';
  } else if (s === 'WAITING' || s === 'WAITING_FOR_APPROVAL' || s === 'PAUSED' || s === 'PENDING') {
    displayStatus = 'WAITING';
  }

  return `Replay completed for execution [${execId}]. Final status: ${displayStatus}.`;
};

const filterTabs = [
  { label: 'All Runs', value: 'all' },
  { label: 'Success', value: 'success', dot: '#22C55E' },
  { label: 'Running', value: 'running', dot: '#06B6D4' },
  { label: 'Failed', value: 'error', dot: '#EF4444' },
  { label: 'Pending', value: 'pending', dot: '#F59E0B' },
  { label: 'Cancelled', value: 'cancelled', dot: '#71717A' },
];

const PAGE_SIZE = 10;

export default function History() {
  const [search, setSearch] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [selectedExecIds, setSelectedExecIds] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<'executed_at' | 'duration' | 'name' | 'status' | 'id'>('executed_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Inspection Drawer state
  const [inspectingItem, setInspectingItem] = useState<WorkflowHistoryItem | null>(null);

  // Notification Banner state
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [replayingId, setReplayingId] = useState<string | null>(null);

  const {
    data: rawHistory = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<WorkflowHistoryItem[]>({
    queryKey: ['workflow_history'],
    queryFn: workflowApi.getHistory,
    refetchInterval: 15000,
  });

  // Fetch failed executions details for inspector enrichment
  const { data: failedHistory = [] } = useQuery<any[]>({
    queryKey: ['failed_history'],
    queryFn: workflowApi.getFailedHistory,
    enabled: Boolean(inspectingItem),
  });

  // Data Normalization
  const historyList = useMemo(() => {
    return rawHistory.map((item) => {
      const rawWfName = item.workflow_name || '';
      let workflowId = item.id;
      if (rawWfName.startsWith('Workflow ')) {
        workflowId = rawWfName.replace('Workflow ', '').trim();
      }

      const parsedTime = item.executed_at
        ? isNaN(Date.parse(item.executed_at)) && !isNaN(Number(item.executed_at))
          ? Number(item.executed_at) * 1000
          : new Date(item.executed_at).getTime()
        : Date.now();

      return {
        ...item,
        execId: item.id,
        workflowId,
        displayTitle: item.workflow_name || `Workflow ${workflowId}`,
        trigger: item.provider || 'Generic Trigger',
        normalizedStatus: normalizeStatus(item.status),
        rawStatus: item.status || 'COMPLETED',
        durationMs: item.duration_ms || 0,
        rawTime: parsedTime,
        formattedTime: parsedTime ? new Date(parsedTime).toLocaleString() : 'Recent',
      };
    });
  }, [rawHistory]);

  // Derived Loaded Summary Metrics
  const summaryMetrics = useMemo(() => {
    const total = historyList.length;
    const successCount = historyList.filter((h) => h.normalizedStatus === 'success').length;
    const failedCount = historyList.filter((h) => h.normalizedStatus === 'error').length;
    const pendingCount = historyList.filter((h) => h.normalizedStatus === 'pending').length;

    const validDurations = historyList.filter((h) => h.durationMs > 0).map((h) => h.durationMs);
    const avgDurationMs =
      validDurations.length > 0 ? validDurations.reduce((a, b) => a + b, 0) / validDurations.length : 0;

    return {
      total,
      successCount,
      failedCount,
      pendingCount,
      avgDurationFormatted:
        avgDurationMs >= 1000 ? `${(avgDurationMs / 1000).toFixed(2)}s` : `${Math.round(avgDurationMs)}ms`,
    };
  }, [historyList]);

  // Search & Filter
  const filtered = useMemo(() => {
    let result = historyList.filter((h) => {
      const q = search.toLowerCase().trim();
      const matchSearch =
        !q ||
        h.execId.toLowerCase().includes(q) ||
        h.workflowId.toLowerCase().includes(q) ||
        h.displayTitle.toLowerCase().includes(q) ||
        h.trigger.toLowerCase().includes(q);

      const matchFilter = activeFilter === 'all' || h.normalizedStatus === activeFilter;
      return matchSearch && matchFilter;
    });

    result.sort((a, b) => {
      let cmp = 0;
      if (sortBy === 'executed_at') cmp = a.rawTime - b.rawTime;
      else if (sortBy === 'duration') cmp = a.durationMs - b.durationMs;
      else if (sortBy === 'name') cmp = a.displayTitle.localeCompare(b.displayTitle);
      else if (sortBy === 'status') cmp = a.normalizedStatus.localeCompare(b.normalizedStatus);
      else if (sortBy === 'id') cmp = a.execId.localeCompare(b.execId);

      return sortOrder === 'desc' ? -cmp : cmp;
    });

    return result;
  }, [historyList, search, activeFilter, sortBy, sortOrder]);

  // Pagination
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
  const pagedRows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const allSelected = pagedRows.length > 0 && pagedRows.every((r) => selectedExecIds.includes(r.execId));

  const toggleAll = () =>
    setSelectedExecIds(
      allSelected
        ? selectedExecIds.filter((id) => !pagedRows.map((r) => r.execId).includes(id))
        : [...new Set([...selectedExecIds, ...pagedRows.map((r) => r.execId)])]
    );

  const toggleSelect = (id: string) =>
    setSelectedExecIds((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const handleSortToggle = (col: 'executed_at' | 'duration' | 'name' | 'status' | 'id') => {
    if (sortBy === col) {
      setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(col);
      setSortOrder('desc');
    }
  };

  // Replay Execution Handler
  const handleReplayExecution = async (executionId: string) => {
    try {
      setNotice(null);
      setReplayingId(executionId);
      const res = await workflowApi.replayExecution(executionId);

      const resId = res?.execution_id || executionId;
      const finalStatus = res?.status;
      setNotice({
        type: 'success',
        message: formatReplayNotificationMessage(resId, finalStatus),
      });
      refetch();
    } catch (err: any) {
      setNotice({
        type: 'error',
        message: `✕ Replay failed: ${err.message || 'Execution replay request failed.'}`,
      });
    } finally {
      setReplayingId(null);
    }
  };

  // Bulk Replay Handler
  const handleBulkReplay = async () => {
    if (selectedExecIds.length === 0) return;
    setNotice(null);
    let successCount = 0;
    let failCount = 0;

    for (const execId of selectedExecIds) {
      try {
        await workflowApi.replayExecution(execId);
        successCount++;
      } catch {
        failCount++;
      }
    }

    if (successCount > 0) {
      setNotice({
        type: 'success',
        message: `✓ Replayed ${successCount} execution${successCount > 1 ? 's' : ''} successfully${
          failCount > 0 ? ` (${failCount} failed)` : ''
        }.`,
      });
      setSelectedExecIds([]);
      refetch();
    } else {
      setNotice({
        type: 'error',
        message: `✕ Failed to replay ${failCount} selected execution(s).`,
      });
    }
  };

  // Build Telemetry Payload for Inspector Adapter
  const inspectorPayload = useMemo(() => {
    if (!inspectingItem) return null;

    const matchedFailed = failedHistory.find(
      (f) => f.id === inspectingItem.id || f.execution_id === inspectingItem.id
    );

    const statusUpper = (inspectingItem.status as string || '').toUpperCase();
    const isOk = statusUpper === 'COMPLETED' || statusUpper === 'SUCCESS';
    const isWaiting =
      statusUpper === 'WAITING' ||
      statusUpper === 'WAITING_FOR_APPROVAL' ||
      statusUpper === 'PAUSED';

    const providers = (inspectingItem.provider || 'Generic')
      .split(',')
      .map((p) => p.trim())
      .filter(Boolean);

    let nodeResultsList: any[] = [];

    if (matchedFailed && matchedFailed.node_records) {
      nodeResultsList = Object.entries(matchedFailed.node_records).map(([nid, rec]: [string, any]) => ({
        node_id: nid,
        operation: rec.operation || rec.provider || 'generic.http.request',
        status: rec.status || 'FAILED',
        output: rec.output || { error: rec.error },
        latency_ms: rec.latency || 0,
        retries: rec.attempts ? rec.attempts - 1 : 0,
      }));
    } else {
      nodeResultsList = providers.map((prov, idx) => ({
        node_id: `step_${idx + 1}`,
        operation: `${prov.toLowerCase()}.action`,
        provider: prov,
        status: isOk ? 'SUCCESS' : isWaiting ? 'WAITING' : 'FAILED',
        output: { provider: prov, status: inspectingItem.status },
        latency_ms: Math.round((inspectingItem.duration_ms || 100) / (providers.length || 1)),
      }));
    }

    return {
      ok: isOk,
      success: isOk,
      status: inspectingItem.status || 'COMPLETED',
      execution_id: inspectingItem.id,
      workflow_id: matchedFailed?.workflow_id || inspectingItem.workflow_name?.replace('Workflow ', '') || inspectingItem.id,
      nodes_executed: nodeResultsList.length > 0 ? nodeResultsList.length : (inspectingItem.steps_count || 1),
      total_nodes: inspectingItem.steps_count || Math.max(nodeResultsList.length, 1),
      node_results: nodeResultsList,
      final_output: matchedFailed || { executed_at: inspectingItem.executed_at },
      can_resume: Boolean(isWaiting || matchedFailed),
    };
  }, [inspectingItem, failedHistory]);

  const filterCounts = useMemo(() => {
    return {
      all: historyList.length,
      success: historyList.filter((h) => h.normalizedStatus === 'success').length,
      running: historyList.filter((h) => h.normalizedStatus === 'running').length,
      error: historyList.filter((h) => h.normalizedStatus === 'error').length,
      pending: historyList.filter((h) => h.normalizedStatus === 'pending').length,
      cancelled: historyList.filter((h) => h.normalizedStatus === 'cancelled').length,
    };
  }, [historyList]);

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-[1440px] mx-auto pb-12">
        {/* ── 1. HEADER & CONTROL BAR ─────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.12)] shadow-xl">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center font-bold shadow-[0_0_15px_rgba(255,109,0,0.20)]">
              <Clock className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl font-bold tracking-tight text-white">Execution History</h1>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30">
                  {summaryMetrics.total} Loaded Runs
                </span>
              </div>
              <p className="text-xs text-[#A098AE] mt-1 font-medium">
                Monitor, inspect, and replay workflow execution runs across all active services.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => refetch()}
              disabled={isLoading}
              className="h-10 px-4 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-xs font-semibold text-[#A098AE] hover:text-white transition flex items-center gap-2 cursor-pointer"
              title="Refresh Execution Logs"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-[#FF6D00] ${isLoading ? 'animate-spin' : ''}`} />
              <span>Sync Telemetry</span>
            </button>

            {selectedExecIds.length > 0 && (
              <button
                onClick={handleBulkReplay}
                className="h-10 px-4 rounded-xl border border-red-500/30 bg-red-500/15 hover:bg-red-500/25 text-red-300 text-xs font-bold transition flex items-center gap-2 shadow-md cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Replay ({selectedExecIds.length})
              </button>
            )}
          </div>
        </div>

        {/* ── NOTIFICATION BANNER ───────────────────────────────────── */}
        {notice && (
          <div
            className={`p-3.5 rounded-xl border text-xs flex items-center justify-between font-medium shadow-lg ${
              notice.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-red-500/10 border-red-500/30 text-red-400'
            }`}
          >
            <div className="flex items-center gap-2 font-mono">
              {notice.type === 'success' ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
              <span>{notice.message}</span>
            </div>
            <button
              onClick={() => setNotice(null)}
              className="p-1 rounded hover:bg-white/10 text-white/60 hover:text-white transition cursor-pointer"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* ── 2. DERIVED LOADED EXECUTION SUMMARY CARDS ───────────────── */}
        {!isLoading && !isError && historyList.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
            <div className="p-4 rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.10)] space-y-1 shadow-lg">
              <span className="text-[10px] font-mono text-[#A098AE] uppercase tracking-wider block">Loaded Runs</span>
              <span className="text-xl font-bold font-mono text-white">{summaryMetrics.total}</span>
            </div>

            <div className="p-4 rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.10)] space-y-1 shadow-lg">
              <span className="text-[10px] font-mono text-[#34D399] uppercase tracking-wider block flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]" /> Successful
              </span>
              <span className="text-xl font-bold font-mono text-[#34D399]">{summaryMetrics.successCount}</span>
            </div>

            <div className="p-4 rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.10)] space-y-1 shadow-lg">
              <span className="text-[10px] font-mono text-red-400 uppercase tracking-wider block flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500" /> Failed
              </span>
              <span className="text-xl font-bold font-mono text-red-400">{summaryMetrics.failedCount}</span>
            </div>

            <div className="p-4 rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.10)] space-y-1 shadow-lg">
              <span className="text-[10px] font-mono text-amber-400 uppercase tracking-wider block flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" /> Pending / Waiting
              </span>
              <span className="text-xl font-bold font-mono text-amber-400">{summaryMetrics.pendingCount}</span>
            </div>

            <div className="p-4 rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.10)] space-y-1 shadow-lg col-span-2 md:col-span-1">
              <span className="text-[10px] font-mono text-[#A098AE] uppercase tracking-wider block">Avg Duration</span>
              <span className="text-xl font-bold font-mono text-white">{summaryMetrics.avgDurationFormatted}</span>
            </div>
          </div>
        )}

        {/* ── 3. SEARCH & FILTER TOOLBAR ─────────────────────────────── */}
        <div className="p-4 rounded-2xl bg-[#13102A]/70 backdrop-blur-xl border border-[rgba(255,255,255,0.10)] flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between shadow-lg">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#7A748E]" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Search by execution ID, workflow ID, title, or provider..."
              className="w-full pl-10 pr-8 py-2 text-xs bg-[#0E0918] text-white placeholder-[#7A748E] rounded-xl border border-[rgba(255,255,255,0.12)] focus:outline-none focus:border-[#FF6D00] focus:ring-1 focus:ring-[#FF6D00] transition shadow-inner font-sans"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 rounded hover:bg-white/10 text-[#A098AE] transition cursor-pointer"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* Filter Pills & Sort Select */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {filterTabs.map((f) => (
                <button
                  key={f.value}
                  onClick={() => {
                    setActiveFilter(f.value);
                    setPage(1);
                  }}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition flex items-center gap-1.5 cursor-pointer ${
                    activeFilter === f.value
                      ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white font-bold shadow-[0_0_10px_rgba(255,109,0,0.30)]'
                      : 'bg-[#0E0918] border border-[rgba(255,255,255,0.12)] text-[#A098AE] hover:text-white hover:border-[#FF6D00]/30'
                  }`}
                >
                  {f.dot && <span className="w-2 h-2 rounded-full" style={{ backgroundColor: f.dot }} />}
                  <span>{f.label}</span>
                  <span className="text-[10px] opacity-75 font-mono">
                    ({filterCounts[f.value as keyof typeof filterCounts] ?? 0})
                  </span>
                </button>
              ))}
            </div>

            {/* Sort Dropdown */}
            <div className="flex items-center gap-1.5 bg-[#0E0918] border border-[rgba(255,255,255,0.12)] rounded-xl px-2.5 py-1.5 text-xs">
              <ArrowUpDown className="h-3.5 w-3.5 text-[#FF6D00]" />
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [col, order] = e.target.value.split('-') as [any, any];
                  setSortBy(col);
                  setSortOrder(order);
                }}
                className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
              >
                <option value="executed_at-desc" className="bg-[#13102A] text-white">Newest First</option>
                <option value="executed_at-asc" className="bg-[#13102A] text-white">Oldest First</option>
                <option value="duration-desc" className="bg-[#13102A] text-white">Duration (Longest)</option>
                <option value="duration-asc" className="bg-[#13102A] text-white">Duration (Shortest)</option>
                <option value="name-asc" className="bg-[#13102A] text-white">Workflow Name (A–Z)</option>
                <option value="id-asc" className="bg-[#13102A] text-white">Execution ID</option>
              </select>
            </div>
          </div>
        </div>

        {/* ── 4. OPERATIONS-GRADE EXECUTION TABLE ─────────────────────── */}
        <div className="rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728]/85 overflow-hidden shadow-2xl backdrop-blur-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[rgba(255,255,255,0.08)] bg-[#13102A]/80 text-[#A098AE] font-bold uppercase tracking-wider">
                  <th className="py-3.5 px-4 w-10 text-center">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onChange={toggleAll}
                      className="rounded border-[rgba(255,255,255,0.20)] bg-[#0E0918] accent-[#FF6D00] cursor-pointer"
                    />
                  </th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-white transition" onClick={() => handleSortToggle('status')}>
                    <div className="flex items-center gap-1">
                      <span>Status</span>
                      {sortBy === 'status' && <ArrowUpDown className="h-3 w-3 text-[#FF6D00]" />}
                    </div>
                  </th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-white transition" onClick={() => handleSortToggle('id')}>
                    <div className="flex items-center gap-1">
                      <span>Execution ID</span>
                      {sortBy === 'id' && <ArrowUpDown className="h-3 w-3 text-[#FF6D00]" />}
                    </div>
                  </th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-white transition" onClick={() => handleSortToggle('name')}>
                    <div className="flex items-center gap-1">
                      <span>Workflow</span>
                      {sortBy === 'name' && <ArrowUpDown className="h-3 w-3 text-[#FF6D00]" />}
                    </div>
                  </th>
                  <th className="py-3.5 px-4">Services / Trigger</th>
                  <th className="py-3.5 px-4 text-center">Steps</th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-white transition" onClick={() => handleSortToggle('duration')}>
                    <div className="flex items-center gap-1 justify-end">
                      <span>Duration</span>
                      {sortBy === 'duration' && <ArrowUpDown className="h-3 w-3 text-[#FF6D00]" />}
                    </div>
                  </th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-white transition" onClick={() => handleSortToggle('executed_at')}>
                    <div className="flex items-center gap-1">
                      <span>Executed At</span>
                      {sortBy === 'executed_at' && <ArrowUpDown className="h-3 w-3 text-[#FF6D00]" />}
                    </div>
                  </th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-[rgba(255,255,255,0.06)]">
                {/* Skeleton Loader */}
                {isLoading && (
                  <>
                    {[1, 2, 3, 4, 5].map((i) => (
                      <tr key={i} className="animate-pulse">
                        <td className="p-4 text-center">
                          <div className="h-4 w-4 rounded bg-[#13102A] mx-auto" />
                        </td>
                        <td className="p-4"><div className="h-5 w-20 rounded-full bg-[#13102A]" /></td>
                        <td className="p-4"><div className="h-4 w-28 rounded bg-[#13102A]" /></td>
                        <td className="p-4"><div className="h-4 w-36 rounded bg-[#13102A]" /></td>
                        <td className="p-4"><div className="h-5 w-24 rounded bg-[#13102A]" /></td>
                        <td className="p-4 text-center"><div className="h-4 w-8 rounded bg-[#13102A] mx-auto" /></td>
                        <td className="p-4"><div className="h-4 w-14 rounded bg-[#13102A] ml-auto" /></td>
                        <td className="p-4"><div className="h-4 w-28 rounded bg-[#13102A]" /></td>
                        <td className="p-4"><div className="h-7 w-20 rounded-xl bg-[#13102A] ml-auto" /></td>
                      </tr>
                    ))}
                  </>
                )}

                {/* Error State */}
                {isError && !isLoading && (
                  <tr>
                    <td colSpan={9} className="p-12 text-center text-red-400 space-y-3">
                      <AlertCircle className="w-8 h-8 mx-auto text-red-400" />
                      <div>
                        <h3 className="text-sm font-bold text-white">Unable to load execution history telemetry</h3>
                        <p className="text-xs text-red-300 mt-1 font-mono">
                          {error instanceof Error ? error.message : 'Backend endpoint /api/v1/history request failed.'}
                        </p>
                      </div>
                      <button
                        onClick={() => refetch()}
                        className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 text-xs font-bold rounded-xl transition inline-flex items-center gap-1.5 cursor-pointer"
                      >
                        <RefreshCw className="h-3.5 w-3.5" /> Retry Catalog Load
                      </button>
                    </td>
                  </tr>
                )}

                {/* Empty State */}
                {!isLoading && !isError && pagedRows.length === 0 && (
                  <tr>
                    <td colSpan={9} className="p-12 text-center text-[#A098AE] space-y-3">
                      <Clock className="w-10 h-10 mx-auto text-[#A098AE]/40" />
                      <div>
                        <h3 className="text-sm font-bold text-white">No execution history records found</h3>
                        <p className="text-xs text-[#A098AE] mt-1">
                          {search || activeFilter !== 'all'
                            ? 'No runs match your search or filter criteria. Try clearing active filters.'
                            : 'Execute a workflow in the studio to start recording telemetry runs.'}
                        </p>
                      </div>
                      {(search || activeFilter !== 'all') && (
                        <button
                          onClick={() => {
                            setSearch('');
                            setActiveFilter('all');
                          }}
                          className="px-4 py-2 bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30 hover:bg-[#FF6D00]/25 text-xs font-bold rounded-xl transition inline-flex items-center gap-1.5 cursor-pointer"
                        >
                          Clear Search & Filters
                        </button>
                      )}
                    </td>
                  </tr>
                )}

                {/* Data Rows */}
                {!isLoading &&
                  !isError &&
                  pagedRows.map((row) => {
                    const cfg = statusConfig[row.normalizedStatus];
                    const StatusIcon = cfg.icon;
                    const isSel = selectedExecIds.includes(row.execId);
                    const formattedDur =
                      row.durationMs > 0
                        ? row.durationMs >= 1000
                          ? `${(row.durationMs / 1000).toFixed(2)}s`
                          : `${Math.round(row.durationMs)}ms`
                        : '—';

                    const providers = row.trigger.split(',').map((p) => p.trim());

                    return (
                      <tr
                        key={row.execId}
                        className={`hover:bg-[#231E3A]/40 transition ${isSel ? 'bg-[#FF6D00]/10' : ''}`}
                      >
                        {/* Checkbox */}
                        <td className="py-3.5 px-4 text-center">
                          <input
                            type="checkbox"
                            checked={isSel}
                            onChange={() => toggleSelect(row.execId)}
                            className="rounded border-[rgba(255,255,255,0.20)] bg-[#0E0918] accent-[#FF6D00] cursor-pointer"
                          />
                        </td>

                        {/* Status Badge */}
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono border ${cfg.bg} ${cfg.border} ${cfg.text}`}
                          >
                            <StatusIcon className="w-3 h-3" />
                            {row.rawStatus || cfg.label}
                          </span>
                        </td>

                        {/* Execution ID */}
                        <td className="py-3.5 px-4 font-mono font-bold text-[#FF6D00] whitespace-nowrap">
                          {row.execId}
                        </td>

                        {/* Workflow Name & Workflow ID */}
                        <td className="py-3.5 px-4 font-bold text-white">
                          <div>
                            <span className="block text-xs font-bold text-white">{row.displayTitle}</span>
                            <span className="text-[10px] font-mono text-[#A098AE] font-normal">
                              wf: <span className="text-white/80">{row.workflowId}</span>
                            </span>
                          </div>
                        </td>

                        {/* Services / Trigger */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-1 flex-wrap">
                            {providers.map((p, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 rounded-md bg-[#13102A] border border-[rgba(255,255,255,0.10)] text-[10px] font-mono text-[#A098AE]"
                              >
                                {p}
                              </span>
                            ))}
                          </div>
                        </td>

                        {/* Steps */}
                        <td className="py-3.5 px-4 text-center font-mono font-bold text-white">
                          <span className="px-2 py-0.5 rounded-md bg-[#13102A] border border-[rgba(255,255,255,0.10)] text-[11px]">
                            {row.steps_count || 1}
                          </span>
                        </td>

                        {/* Duration */}
                        <td className="py-3.5 px-4 text-right font-mono text-[#A098AE] font-semibold whitespace-nowrap">
                          {formattedDur}
                        </td>

                        {/* Executed At */}
                        <td className="py-3.5 px-4 text-[#A098AE] font-mono text-[11px] whitespace-nowrap">
                          {row.formattedTime}
                        </td>

                        {/* Actions */}
                        <td className="py-3.5 px-4 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-1.5">
                            {/* Inspect Action */}
                            <button
                              onClick={() => setInspectingItem(row)}
                              className="px-3 py-1.5 rounded-xl bg-[#1B1728] hover:bg-[#231E3A] border border-[rgba(255,255,255,0.12)] hover:border-[#FF6D00]/40 text-[#A098AE] hover:text-white text-xs font-bold transition flex items-center gap-1.5 cursor-pointer"
                              title="Inspect Execution Telemetry"
                            >
                              <Eye className="w-3.5 h-3.5 text-[#FF6D00]" /> Inspect
                            </button>

                            {/* Replay Action */}
                            {row.normalizedStatus === 'error' && (
                              <button
                                onClick={() => handleReplayExecution(row.execId)}
                                disabled={replayingId === row.execId}
                                className="p-1.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 transition cursor-pointer disabled:opacity-50"
                                title="Replay Execution from Checkpoint"
                              >
                                {replayingId === row.execId ? (
                                  <Loader2 className="w-3.5 h-3.5 animate-spin text-red-400" />
                                ) : (
                                  <RotateCcw className="w-3.5 h-3.5" />
                                )}
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>

          {/* ── 5. PAGINATION CONTROLS ───────────────────────────────── */}
          <div className="p-4 border-t border-[rgba(255,255,255,0.08)] bg-[#13102A]/80 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#A098AE]">
            <span>
              Showing {filtered.length === 0 ? 0 : (page - 1) * PAGE_SIZE + 1}–
              {Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length} loaded executions
            </span>

            <div className="flex items-center gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded-xl border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-white hover:bg-[#231E3A] disabled:opacity-30 transition cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-bold text-white font-mono text-xs">
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="p-1.5 rounded-xl border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-white hover:bg-[#231E3A] disabled:opacity-30 transition cursor-pointer"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* ── 6. EXECUTION INSPECTOR SLIDE-OVER DRAWER ────────────────── */}
        {inspectingItem && inspectorPayload && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xl flex justify-end">
            <div className="w-full max-w-2xl bg-[#13102A] border-l border-[rgba(255,255,255,0.12)] h-full overflow-y-auto flex flex-col shadow-2xl">
              {/* Drawer Header */}
              <div className="p-4 border-b border-[rgba(255,255,255,0.10)] bg-[#13102A] flex items-center justify-between sticky top-0 z-10 backdrop-blur-md">
                <div className="flex items-center gap-2.5">
                  <div className="h-8 w-8 rounded-xl bg-[#FF6D00]/20 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center font-bold">
                    <Eye className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-white">Execution Inspector</h3>
                    <p className="text-[10px] text-[#A098AE] font-mono">
                      Run ID: <span className="text-[#FF6D00]">{inspectingItem.id}</span>
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setInspectingItem(null)}
                  className="p-1.5 rounded-lg hover:bg-white/10 text-[#A098AE] hover:text-white transition cursor-pointer"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Inspector Content Surface */}
              <div className="p-4 flex-1">
                <ExecutionResultInspector
                  executionResult={inspectorPayload}
                  onClose={() => setInspectingItem(null)}
                  onExecuteSuccess={() => refetch()}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
