import React, { useEffect, useRef, useState } from 'react';
import { useExecutionStore } from '../../store/useExecutionStore';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import { workflowApi } from '../../api/workflows';
import {
  Play, Pause, RotateCcw, Download, CheckCircle2,
  AlertCircle, Clock, Square, Zap, Layers, ChevronDown
} from 'lucide-react';

function formatElapsed(ms: number): string {
  if (!ms) return '0ms';
  if (ms < 1000) return `${ms}ms`;
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  if (m === 0) return `${s}s`;
  return `${m}m ${s % 60}s`;
}

const PRESET_DEFINITIONS = [
  {
    id: 'wf_1',
    label: 'WF 1: Gmail → Drive → Slack → Sheets',
    nodes: [
      { id: 'step_1', provider: 'Gmail', label: 'Gmail: Watch Invoices' },
      { id: 'step_2', provider: 'Google Drive', label: 'Drive: Save PDF' },
      { id: 'step_3', provider: 'Slack', label: 'Slack: Send Alert' },
      { id: 'step_4', provider: 'Google Sheets', label: 'Sheets: Append Row' },
    ],
  },
  {
    id: 'wf_2',
    label: 'WF 2: GitHub → Slack → Notion',
    nodes: [
      { id: 'step_1', provider: 'GitHub', label: 'GitHub: Issue Webhook' },
      { id: 'step_2', provider: 'Slack', label: 'Slack: Alert Channel' },
      { id: 'step_3', provider: 'Notion', label: 'Notion: Create Page' },
    ],
  },
  {
    id: 'wf_3',
    label: 'WF 3: Webhook → AI → Email → Database',
    nodes: [
      { id: 'step_1', provider: 'Webhook', label: 'Webhook: Event Trigger' },
      { id: 'step_2', provider: 'AI Agent', label: 'AI: Transform Invoice' },
      { id: 'step_3', provider: 'Email', label: 'Email: Send Receipt' },
      { id: 'step_4', provider: 'Database', label: 'Database: Insert Record' },
    ],
  },
  {
    id: 'wf_4',
    label: 'WF 4: Sheets → Loop → Gmail',
    nodes: [
      { id: 'step_1', provider: 'Google Sheets', label: 'Sheets: Fetch Customers' },
      { id: 'step_2', provider: 'Loop', label: 'Loop: Iterate Items' },
      { id: 'step_3', provider: 'Gmail', label: 'Gmail: Send Custom Mail' },
    ],
  },
];

const STATUS_CFG: Record<string, { color: string; bg: string; border: string; label: string; icon: React.ReactNode }> = {
  RUNNING:     { color: 'text-blue-400',    bg: 'bg-blue-500/10',    border: 'border-blue-500/30',    label: 'Executing', icon: <Zap className="h-3.5 w-3.5 animate-pulse" /> },
  PAUSED:      { color: 'text-amber-400',   bg: 'bg-amber-500/10',   border: 'border-amber-500/30',   label: 'Paused',    icon: <Clock className="h-3.5 w-3.5" /> },
  COMPLETED:   { color: 'text-[#22C55E]',   bg: 'bg-[#22C55E]/10',   border: 'border-[#22C55E]/30',   label: 'Completed', icon: <CheckCircle2 className="h-3.5 w-3.5" /> },
  FAILED:      { color: 'text-rose-400',    bg: 'bg-rose-500/10',    border: 'border-rose-500/30',    label: 'Failed',    icon: <AlertCircle className="h-3.5 w-3.5" /> },
  CANCELLED:   { color: 'text-slate-400',   bg: 'bg-slate-400/10',   border: 'border-slate-400/30',   label: 'Cancelled', icon: <Square className="h-3.5 w-3.5" /> },
  ROLLED_BACK: { color: 'text-purple-400', bg: 'bg-purple-400/10', border: 'border-purple-400/30',  label: 'Rolled Back', icon: <RotateCcw className="h-3.5 w-3.5" /> },
  IDLE:        { color: 'text-[rgba(255,255,255,0.5)]', bg: 'bg-[rgba(255,255,255,0.06)]', border: 'border-[rgba(255,255,255,0.12)]', label: 'Idle / Ready', icon: <Clock className="h-3.5 w-3.5" /> },
};

export const ExecutionControls: React.FC = () => {
  const { nodes } = useWorkflowStore();
  const {
    executionId, status, stepRecords, elapsedMs, startedAt,
    startExecution, pauseExecution, resumeExecution, cancelExecution,
    replayExecution, downloadLogs, simulateExecution,
  } = useExecutionStore();

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Elapsed clock
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    if (status === 'RUNNING') {
      timerRef.current = setInterval(() => {
        useExecutionStore.setState({ elapsedMs: Date.now() - (startedAt ?? Date.now()) });
      }, 500);
    } else {
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [status, startedAt]);

  const stepIds = nodes.length > 0 ? nodes.map((n) => n.id) : ['step_1', 'step_2', 'step_3', 'step_4'];
  const nodeLabels: Record<string, string> = {};
  nodes.forEach((n) => { nodeLabels[n.id] = String(n.data?.label || n.id); });

  const totalSteps = stepIds.length;
  const completedSteps = Object.values(stepRecords).filter(
    (r) => r.status === 'COMPLETED' || r.status === 'FAILED' || r.status === 'CANCELLED'
  ).length;
  const progress = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

  const cfg = STATUS_CFG[status] ?? STATUS_CFG.IDLE;
  const isIdle = status === 'IDLE';
  const canReplay = status === 'FAILED' || status === 'ROLLED_BACK';

  const handleRun = async () => {
    const { edges } = useWorkflowStore.getState();
    const spec = {
      workflow_id: `wf_${Math.random().toString(36).substring(2, 7)}`,
      nodes: nodes.map((n) => ({
        id: n.id,
        step_id: n.id,
        provider: (n.data as any).provider || 'Generic',
        operation_id: (n.data as any).operation_id || 'generic.http.request',
        parameters: (n.data as any).parameters || {},
        dependencies: edges.filter((e) => e.target === n.id).map((e) => e.source),
      })),
      edges: edges.map((e) => ({ source: e.source, target: e.target })),
      steps: nodes.map((n) => ({
        step_id: n.id,
        id: n.id,
        provider: (n.data as any).provider || 'Generic',
        operation_id: (n.data as any).operation_id || 'generic.http.request',
        parameters: (n.data as any).parameters || {},
        dependencies: edges.filter((e) => e.target === n.id).map((e) => e.source),
      })),
    };

    startExecution(stepIds);
    try {
      const res = await workflowApi.executeWorkflow(spec);
      useExecutionStore.getState().applyRealExecutionResult(
        res.execution_id || 'exec_live',
        res.status || 'COMPLETED',
        res.node_results || [],
        res.final_output
      );
    } catch {
      simulateExecution(stepIds, nodeLabels);
    }
  };

  const handleRunPreset = (presetId: string) => {
    const preset = PRESET_DEFINITIONS.find((p) => p.id === presetId) || PRESET_DEFINITIONS[0];
    setIsDropdownOpen(false);

    const formattedNodes = preset.nodes.map((n, idx) => ({
      id: n.id,
      type: 'customNode',
      position: { x: 250 * idx + 100, y: 150 },
      data: {
        label: n.label,
        provider: n.provider,
        operation_id: 'action',
        parameters: {},
      },
    }));

    useWorkflowStore.setState({ nodes: formattedNodes });
    const pStepIds = preset.nodes.map((n) => n.id);
    const pNodeLabels: Record<string, string> = {};
    preset.nodes.forEach((n) => { pNodeLabels[n.id] = n.label; });

    startExecution(pStepIds);
    simulateExecution(pStepIds, pNodeLabels);
  };

  return (
    <div className="p-4 border-b border-[rgba(255,255,255,0.12)] bg-[#13102A]/90 backdrop-blur-md flex flex-col md:flex-row md:items-center justify-between gap-4">
      
      {/* Title & Metadata */}
      <div className="flex items-center gap-4 min-w-0">
        <div className="h-11 w-11 rounded-2xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] text-white flex items-center justify-center font-extrabold shadow-[0_4px_16px_rgba(255,109,0,0.4)] shrink-0">
          <Zap className="h-6 w-6 fill-current" />
        </div>

        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="font-extrabold text-base text-white tracking-tight">Execution Studio</h2>
            
            {/* Status Pill */}
            <div className={`px-2.5 py-0.5 rounded-full border text-[11px] font-bold flex items-center gap-1.5 ${cfg.bg} ${cfg.color} ${cfg.border}`}>
              {cfg.icon}
              <span>{cfg.label}</span>
            </div>

            {!isIdle && executionId && (
              <span className="text-[10px] font-mono text-[rgba(255,255,255,0.5)] px-2 py-0.5 rounded bg-[rgba(255,255,255,0.06)] border border-[rgba(255,255,255,0.08)]">
                {executionId}
              </span>
            )}
          </div>
          
          <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5 truncate">
            Monitor workflow execution, inspect steps, and troubleshoot runtime behavior.
          </p>
        </div>
      </div>

      {/* Real Execution Progress & Controls */}
      <div className="flex items-center gap-3 self-start md:self-auto flex-wrap">
        
        {/* Progress & Duration Badge (if running or completed) */}
        {!isIdle && (
          <div className="flex items-center gap-3 px-3 py-1.5 rounded-xl bg-[#1B1728] border border-[rgba(255,255,255,0.1)] text-xs font-mono">
            <span className="text-[rgba(255,255,255,0.6)]">
              Progress: <strong className="text-white">{progress}%</strong>
            </span>
            <span className="text-[rgba(255,255,255,0.2)]">|</span>
            <span className="text-[rgba(255,255,255,0.6)]">
              Elapsed: <strong className="text-[#FF6D00]">{formatElapsed(elapsedMs)}</strong>
            </span>
          </div>
        )}

        {/* Action Controls */}
        {isIdle ? (
          <div className="flex items-center gap-2">
            <button
              onClick={handleRun}
              className="px-4 py-2 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl shadow-[0_4px_16px_rgba(255,109,0,0.3)] hover:opacity-95 transition flex items-center gap-1.5"
            >
              <Play className="h-3.5 w-3.5 fill-current" /> Execute Workflow
            </button>

            {/* Presets Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsDropdownOpen((v) => !v)}
                className="px-3 py-2 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-xs font-semibold text-white transition flex items-center gap-1.5"
              >
                <Layers className="h-3.5 w-3.5 text-[#FF6D00]" />
                <span>Preset Demo</span>
                <ChevronDown className="h-3 w-3" />
              </button>

              {isDropdownOpen && (
                <div className="absolute right-0 top-full mt-2 w-72 rounded-2xl bg-[#1B1728] border border-[rgba(255,255,255,0.12)] shadow-2xl p-2 z-50 space-y-1">
                  {PRESET_DEFINITIONS.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => handleRunPreset(p.id)}
                      className="w-full text-left px-3 py-2 rounded-xl text-xs text-[rgba(255,255,255,0.8)] hover:text-white hover:bg-[#231E3A] transition truncate"
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : status === 'RUNNING' ? (
          <div className="flex items-center gap-2">
            <button
              onClick={pauseExecution}
              className="px-3.5 py-2 rounded-xl border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-xs font-semibold transition flex items-center gap-1.5"
            >
              <Pause className="h-3.5 w-3.5" /> Pause
            </button>
            <button
              onClick={cancelExecution}
              className="px-3.5 py-2 rounded-xl border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-semibold transition flex items-center gap-1.5"
            >
              <Square className="h-3.5 w-3.5" /> Stop
            </button>
          </div>
        ) : status === 'PAUSED' ? (
          <button
            onClick={resumeExecution}
            className="px-4 py-2 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl shadow-[0_4px_16px_rgba(255,109,0,0.3)] hover:opacity-95 transition flex items-center gap-1.5"
          >
            <Play className="h-3.5 w-3.5 fill-current" /> Resume Execution
          </button>
        ) : (
          <div className="flex items-center gap-2">
            {canReplay && (
              <button
                onClick={() => replayExecution()}
                className="px-3.5 py-2 rounded-xl border border-[#FF6D00]/40 bg-[#FF6D00]/10 hover:bg-[#FF6D00]/20 text-[#FF6D00] text-xs font-bold transition flex items-center gap-1.5"
              >
                <RotateCcw className="h-3.5 w-3.5" /> Replay Checkpoint
              </button>
            )}

            <button
              onClick={() => useExecutionStore.setState({ status: 'IDLE', stepRecords: {}, elapsedMs: 0 })}
              className="px-3.5 py-2 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-xs font-semibold text-white transition flex items-center gap-1.5"
            >
              Reset
            </button>

            <button
              onClick={downloadLogs}
              className="p-2 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-[rgba(255,255,255,0.7)] hover:text-white transition"
              title="Download Execution Logs"
            >
              <Download className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
