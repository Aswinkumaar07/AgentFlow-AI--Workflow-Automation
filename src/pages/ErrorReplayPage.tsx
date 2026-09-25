import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { workflowApi } from '../api/workflows';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { formatReplayNotificationMessage } from './History';
import {
  AlertOctagon, RotateCcw, CheckCircle2, ShieldAlert,
  Code2, Clock, AlertTriangle, RefreshCw, Layers, Terminal, X, Eye
} from 'lucide-react';

export const ErrorReplayPage: React.FC = () => {
  const [replayingId, setReplayingId] = useState<string | null>(null);
  const [fadingIds, setFadingIds] = useState<Set<string>>(new Set());
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [inspectedRecord, setInspectedRecord] = useState<any | null>(null);

  const { data: failedRecords = [], isLoading, refetch } = useQuery({
    queryKey: ['failed_history'],
    queryFn: workflowApi.getFailedHistory,
  });

  const handleReplay = async (id: string) => {
    const rec = failedRecords.find((r: any) => r.id === id || r.execution_id === id);
    const execId = rec?.execution_id || rec?.id || id;

    setReplayingId(execId);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      const res = await workflowApi.replayExecution(execId);
      const finalStatus = res?.status;
      setFadingIds((prev) => new Set(prev).add(execId));
      setSuccessMessage(formatReplayNotificationMessage(execId, finalStatus));
      await new Promise((resolve) => setTimeout(resolve, 400));
      await refetch();
    } catch (err: any) {
      setErrorMessage(`Failed to replay execution [${execId}]: ${err.message || 'Unknown error'}`);
    } finally {
      setReplayingId(null);
      setFadingIds((prev) => {
        const next = new Set(prev);
        next.delete(execId);
        return next;
      });
    }
  };

  const handleReplayAll = async () => {
    if (!failedRecords.length) return;
    setReplayingId('all');
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      const allIds = failedRecords.map((rec: any) => rec.execution_id || rec.id);
      setFadingIds(new Set(allIds));
      for (const id of allIds) {
        await workflowApi.replayExecution(id).catch(() => {});
      }
      setSuccessMessage(`Replay processing completed for all ${failedRecords.length} DLQ records.`);
      await new Promise((resolve) => setTimeout(resolve, 400));
      await refetch();
    } catch (err: any) {
      setErrorMessage(`Replay all error: ${err.message || 'Unknown error'}`);
    } finally {
      setReplayingId(null);
      setFadingIds(new Set());
    }
  };

  const formatTimestamp = (ts: any) => {
    if (!ts) return 'Just now';
    if (typeof ts === 'number') {
      return new Date(ts * 1000).toLocaleString();
    }
    return String(ts);
  };

  const failedCount = failedRecords.length;
  const replayableCount = failedRecords.filter((r: any) => r.checkpoint_path || r.execution_id || r.id).length;
  const errorNodeCount = failedRecords.filter((r: any) => r.failed_step || r.error_node_id || r.error_message).length;

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-[1440px] mx-auto">
        
        {/* ── 1. Header Banner ── */}
        <div className="p-6 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md shadow-[0_8px_32px_rgba(0,0,0,0.36)] flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-rose-500/10 to-[#FF0C00]/5 blur-3xl pointer-events-none rounded-full" />

          <div className="flex items-center gap-4 relative z-10">
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-rose-500 to-rose-700 flex items-center justify-center text-white shadow-[0_4px_20px_rgba(239,68,68,0.4)] shrink-0">
              <AlertOctagon className="h-7 w-7" />
            </div>

            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-extrabold text-white tracking-tight">Dead Letter Queue & Error Replay</h1>
                <span className="px-2.5 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-400 text-[10px] font-bold uppercase tracking-wider">
                  DLQ Vault
                </span>
              </div>
              <p className="text-xs text-[rgba(255,255,255,0.6)] mt-1">
                Inspect failed executions, review checkpoints, and safely replay workflows.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 relative z-10 self-start md:self-auto">
            <button
              onClick={() => refetch()}
              disabled={isLoading}
              className="p-2.5 rounded-xl border border-[rgba(255,255,255,0.15)] bg-[#1B1728] hover:bg-[#231E3A] hover:border-[#FF6D00]/50 text-xs font-bold text-white transition shadow-md disabled:opacity-50"
              title="Refresh Failed History"
            >
              <RefreshCw className={`h-4 w-4 text-[#FF6D00] ${isLoading ? 'animate-spin' : ''}`} />
            </button>

            <button
              onClick={handleReplayAll}
              disabled={replayingId === 'all' || !failedRecords.length}
              className="px-5 py-2.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl shadow-[0_4px_16px_rgba(255,109,0,0.3)] hover:opacity-95 transition flex items-center gap-2 disabled:opacity-50"
            >
              <RotateCcw className={`h-4 w-4 ${replayingId === 'all' ? 'animate-spin' : ''}`} />
              {replayingId === 'all' ? 'Replaying All DLQ…' : 'Replay All DLQ Records'}
            </button>
          </div>
        </div>

        {/* ── Summary Metric Cards ── */}
        {!isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl border border-rose-500/20 bg-rose-500/5 backdrop-blur-md flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center shrink-0">
                <AlertOctagon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xl font-extrabold text-rose-400">{failedCount}</p>
                <p className="text-[11px] font-semibold text-rose-400">Failed DLQ Records</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl border border-[#FF6D00]/20 bg-[#FF6D00]/5 backdrop-blur-md flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-[#FF6D00]/10 text-[#FF6D00] flex items-center justify-center shrink-0">
                <RotateCcw className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xl font-extrabold text-[#FF6D00]">{replayableCount}</p>
                <p className="text-[11px] font-semibold text-[#FF6D00]">Replayable Checkpoints</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[#13102A]/60 backdrop-blur-md flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-[rgba(255,255,255,0.05)] text-[rgba(255,255,255,0.6)] flex items-center justify-center shrink-0">
                <Layers className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xl font-extrabold text-white">{errorNodeCount}</p>
                <p className="text-[11px] font-semibold text-[rgba(255,255,255,0.5)]">Captured Step Faults</p>
              </div>
            </div>
          </div>
        )}

        {/* ── Feedback Messages ── */}
        {successMessage && (
          <div className="p-4 bg-[#22C55E]/10 border border-[#22C55E]/30 rounded-2xl text-xs text-[#22C55E] font-bold flex items-center gap-2 shadow-sm animate-in fade-in">
            <CheckCircle2 className="h-4 w-4 shrink-0" /> {successMessage}
          </div>
        )}

        {errorMessage && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-xs text-rose-400 font-bold flex items-center gap-2 shadow-sm animate-in fade-in">
            <AlertTriangle className="h-4 w-4 shrink-0" /> {errorMessage}
          </div>
        )}

        {/* ── DLQ Cards List ── */}
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-44 rounded-3xl border border-[rgba(255,255,255,0.08)] bg-[#13102A]/60 backdrop-blur-md animate-pulse p-6" />
            ))}
          </div>
        ) : failedRecords.length === 0 ? (
          /* Empty State */
          <div className="p-12 text-center border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md rounded-3xl space-y-4 max-w-md mx-auto my-8">
            <div className="h-16 w-16 rounded-3xl bg-[#22C55E]/10 text-[#22C55E] flex items-center justify-center mx-auto border border-[#22C55E]/20">
              <CheckCircle2 className="h-8 w-8" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">No Failed Executions</h3>
              <p className="text-xs text-[rgba(255,255,255,0.5)] mt-1">
                All workflow executions are operating nominally or completed successfully.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {failedRecords.map((rec: any) => {
              const execId = rec.execution_id || rec.id;
              const wfName = rec.workflow_name || `Workflow ${rec.workflow_id || 'Pipeline'}`;
              const failedStep = rec.failed_step || rec.error_node_id || 'Step Execution';
              const errorMsg = rec.error_message || rec.error || 'Execution encountered an unhandled error state.';
              const isReplayingThis = replayingId === execId || replayingId === 'all';
              const isFading = fadingIds.has(execId);

              return (
                <div
                  key={execId}
                  className={`p-6 rounded-3xl border transition-all duration-300 bg-[#13102A]/80 backdrop-blur-md space-y-4 ${
                    isFading ? 'opacity-40 border-emerald-500/50' : 'border-[rgba(255,255,255,0.12)] hover:border-rose-500/40'
                  }`}
                >
                  {/* Top Bar: Identity & Status */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[rgba(255,255,255,0.08)]">
                    <div className="flex items-center gap-3">
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-500/15 border border-rose-500/30 text-rose-400 flex items-center gap-1">
                        <ShieldAlert className="h-3 w-3" /> FAILED DLQ
                      </span>
                      <span className="font-mono text-xs font-bold text-white bg-[#1B1728] px-2.5 py-1 rounded-lg border border-[rgba(255,255,255,0.1)]">
                        {execId}
                      </span>
                      <span className="text-xs font-semibold text-[rgba(255,255,255,0.7)] truncate">
                        {wfName}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] font-mono text-[rgba(255,255,255,0.45)]">
                      <Clock className="h-3.5 w-3.5 text-[rgba(255,255,255,0.4)]" />
                      <span>{formatTimestamp(rec.executed_at || rec.timestamp)}</span>
                    </div>
                  </div>

                  {/* Middle Body: Failure Details */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-1">
                      <span className="text-[10px] uppercase font-bold text-[rgba(255,255,255,0.4)] tracking-wider">Failed Node Step</span>
                      <p className="text-xs font-semibold text-rose-400 font-mono flex items-center gap-1.5">
                        <Code2 className="h-3.5 w-3.5 shrink-0" />
                        <span>{failedStep}</span>
                      </p>
                    </div>

                    <div className="md:col-span-2 space-y-1">
                      <span className="text-[10px] uppercase font-bold text-[rgba(255,255,255,0.4)] tracking-wider">Error Trace Exception</span>
                      <div className="p-3 rounded-xl bg-[#0E0918] border border-rose-500/20 font-mono text-xs text-rose-300 break-all leading-relaxed">
                        {errorMsg}
                      </div>
                    </div>
                  </div>

                  {/* Bottom Actions Row */}
                  <div className="pt-2 flex items-center justify-between gap-3">
                    <button
                      onClick={() => setInspectedRecord(rec)}
                      className="px-3.5 py-1.5 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-xs font-semibold text-white transition flex items-center gap-1.5"
                    >
                      <Eye className="h-3.5 w-3.5 text-[#FF6D00]" /> Inspect Stack Trace
                    </button>

                    <button
                      onClick={() => handleReplay(execId)}
                      disabled={isReplayingThis}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold shadow-[0_4px_14px_rgba(255,109,0,0.3)] hover:opacity-95 transition flex items-center gap-2 disabled:opacity-50"
                    >
                      <RotateCcw className={`h-3.5 w-3.5 ${isReplayingThis ? 'animate-spin' : ''}`} />
                      {isReplayingThis ? 'Replaying Checkpoint…' : 'Replay Checkpoint'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── Stack Trace Inspector Modal ── */}
        {inspectedRecord && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in">
            <div className="w-full max-w-2xl bg-[#13102A] border border-[rgba(255,255,255,0.12)] rounded-3xl p-6 shadow-2xl space-y-4 relative">
              <button
                onClick={() => setInspectedRecord(null)}
                className="absolute top-4 right-4 p-1.5 rounded-xl text-[rgba(255,255,255,0.5)] hover:text-white hover:bg-[#231E3A] transition"
              >
                <X className="h-4 w-4" />
              </button>

              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-rose-500/15 text-rose-400 border border-rose-500/30 flex items-center justify-center font-bold">
                  <Terminal className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-white tracking-tight">
                    Stack Trace — [{inspectedRecord.execution_id || inspectedRecord.id}]
                  </h3>
                  <p className="text-xs text-[rgba(255,255,255,0.5)]">Detailed DLQ fault diagnostic logs</p>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#0E0918] border border-[rgba(255,255,255,0.1)] font-mono text-xs text-rose-300 space-y-2 max-h-80 overflow-y-auto leading-relaxed">
                <p className="text-white font-bold">Failed Step: {inspectedRecord.failed_step || inspectedRecord.error_node_id || 'Step Execution'}</p>
                <p className="text-[rgba(255,255,255,0.6)]">Execution ID: {inspectedRecord.execution_id || inspectedRecord.id}</p>
                <div className="p-3 rounded-xl bg-[#13102A] border border-rose-500/20 text-rose-400 font-mono text-xs">
                  {inspectedRecord.error_message || inspectedRecord.error || 'Execution stopped due to connection error.'}
                </div>
                {inspectedRecord.trace && (
                  <pre className="text-[11px] text-[rgba(255,255,255,0.7)] whitespace-pre-wrap pt-2 border-t border-[rgba(255,255,255,0.1)]">
                    {inspectedRecord.trace}
                  </pre>
                )}
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setInspectedRecord(null)}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold hover:opacity-90 transition"
                >
                  Close Trace
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
