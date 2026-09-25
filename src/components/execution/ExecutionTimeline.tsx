import React, { useMemo } from 'react';
import { useExecutionStore, type StepStatus } from '../../store/useExecutionStore';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import {
  CheckCircle2, AlertCircle, Clock, RotateCcw, Eye,
  Loader2, SkipForward, Square, Timer, Cpu
} from 'lucide-react';

const STATUS_CFG: Record<StepStatus, { color: string; bg: string; border: string; label: string; icon: React.ReactNode }> = {
  PENDING:              { color: 'text-[rgba(255,255,255,0.4)]', bg: 'bg-[rgba(255,255,255,0.06)]', border: 'border-[rgba(255,255,255,0.1)]', label: 'Pending',   icon: <Clock className="h-3 w-3" /> },
  RUNNING:              { color: 'text-blue-400',               bg: 'bg-blue-500/10',               border: 'border-blue-500/30',               label: 'Running',   icon: <Loader2 className="h-3 w-3 animate-spin" /> },
  COMPLETED:            { color: 'text-[#22C55E]',              bg: 'bg-[#22C55E]/10',              border: 'border-[#22C55E]/30',              label: 'Done',      icon: <CheckCircle2 className="h-3 w-3" /> },
  FAILED:               { color: 'text-rose-400',               bg: 'bg-rose-500/10',               border: 'border-rose-500/30',               label: 'Failed',    icon: <AlertCircle className="h-3 w-3" /> },
  SKIPPED:              { color: 'text-slate-400',              bg: 'bg-slate-400/10',              border: 'border-slate-400/30',              label: 'Skipped',   icon: <SkipForward className="h-3 w-3" /> },
  CANCELLED:            { color: 'text-slate-400',              bg: 'bg-slate-400/10',              border: 'border-slate-400/30',              label: 'Cancelled', icon: <Square className="h-3 w-3" /> },
  WAITING_FOR_APPROVAL: { color: 'text-amber-400',              bg: 'bg-amber-500/10',              border: 'border-amber-500/30',              label: 'Waiting',   icon: <Clock className="h-3 w-3" /> },
};

function formatLatency(ms: number): string {
  if (!ms) return '—';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export const ExecutionTimeline: React.FC = () => {
  const { nodes } = useWorkflowStore();
  const { stepRecords, retryStep, setActiveStepId, executionPath, status } = useExecutionStore();

  const stepList = useMemo(() => {
    if (nodes.length > 0) {
      return nodes.map((n) => ({
        id: n.id,
        label: String(n.data?.label || n.data?.operation_id || n.id),
        provider: String(n.data?.provider || ''),
      }));
    }
    return [
      { id: 'step_1', label: 'Gmail: Read Emails',       provider: 'Gmail' },
      { id: 'step_2', label: 'Google Drive: Upload File', provider: 'Drive' },
      { id: 'step_3', label: 'Slack: Send Message',       provider: 'Slack' },
      { id: 'step_4', label: 'Condition: Check Status',   provider: 'Logic' },
    ];
  }, [nodes]);

  const maxLatency = useMemo(() => {
    const latencies = Object.values(stepRecords).map((r) => r.latency_ms).filter(Boolean);
    return latencies.length > 0 ? Math.max(...latencies) : 1;
  }, [stepRecords]);

  const completedCount = Object.values(stepRecords).filter((r) => r.status === 'COMPLETED').length;
  const totalCount = stepList.length;

  return (
    <aside className="w-72 border-r border-[rgba(255,255,255,0.12)] bg-[#1B1728]/90 backdrop-blur-md flex flex-col h-full text-xs">
      
      {/* Header */}
      <div className="p-4 border-b border-[rgba(255,255,255,0.12)] flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-sm text-white">
          <Timer className="h-4 w-4 text-[#FF6D00]" />
          <span>Step Execution Timeline</span>
        </div>
        <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
          status === 'COMPLETED' ? 'bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/30' :
          status === 'FAILED'    ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' :
          status === 'RUNNING'   ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30' :
          'bg-[rgba(255,255,255,0.06)] text-[rgba(255,255,255,0.5)] border border-[rgba(255,255,255,0.1)]'
        }`}>
          {status === 'IDLE' ? `${totalCount} steps` : `${completedCount}/${totalCount}`}
        </span>
      </div>

      {/* Step List */}
      <div className="flex-1 p-3 overflow-y-auto space-y-2 scrollbar-none">
        {stepList.map((step) => {
          const rec = stepRecords[step.id];
          const stepStatus: StepStatus = rec?.status ?? 'PENDING';
          const cfg = STATUS_CFG[stepStatus];
          const isRunning = stepStatus === 'RUNNING';
          const isFailed = stepStatus === 'FAILED';
          const isCompleted = stepStatus === 'COMPLETED';
          const inPath = executionPath.includes(step.id);

          const latencyPct = rec?.latency_ms && maxLatency > 0
            ? Math.round((rec.latency_ms / maxLatency) * 100)
            : 0;

          return (
            <div
              key={step.id}
              className={`p-3 rounded-2xl border transition-all ${
                inPath || isRunning
                  ? 'bg-gradient-to-r from-[rgba(255,109,0,0.15)] to-[#13102A] border-[#FF6D00]/40 shadow-sm'
                  : 'bg-[#13102A]/60 border-[rgba(255,255,255,0.08)] hover:border-[rgba(255,255,255,0.15)]'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <Cpu className="h-3.5 w-3.5 text-[#FF6D00] shrink-0" />
                  <span className="font-semibold text-xs text-white truncate" title={step.label}>
                    {step.label}
                  </span>
                </div>

                <div className={`px-2 py-0.5 rounded-full text-[9px] font-bold border flex items-center gap-1 shrink-0 ${cfg.bg} ${cfg.color} ${cfg.border}`}>
                  {cfg.icon}
                  <span>{cfg.label}</span>
                </div>
              </div>

              {/* Latency bar */}
              {rec?.latency_ms ? (
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between text-[10px] font-mono text-[rgba(255,255,255,0.45)]">
                    <span>Latency:</span>
                    <span className="text-white font-semibold">{formatLatency(rec.latency_ms)}</span>
                  </div>
                  <div className="w-full h-1 rounded-full bg-[#0E0918] overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isFailed ? 'bg-rose-500' : isCompleted ? 'bg-[#22C55E]' : 'bg-[#FF6D00]'
                      }`}
                      style={{ width: `${Math.max(5, latencyPct)}%` }}
                    />
                  </div>
                </div>
              ) : null}

              {/* Actions */}
              <div className="mt-2.5 pt-2 border-t border-[rgba(255,255,255,0.06)] flex items-center justify-between">
                <button
                  onClick={() => setActiveStepId(step.id)}
                  className="text-[10px] font-semibold text-[#FF6D00] hover:underline flex items-center gap-1"
                >
                  <Eye className="h-3 w-3" /> Inspect Payload
                </button>

                {isFailed && (
                  <button
                    onClick={() => retryStep(step.id)}
                    className="text-[10px] font-semibold text-rose-400 hover:underline flex items-center gap-1"
                  >
                    <RotateCcw className="h-3 w-3" /> Retry Step
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
};
