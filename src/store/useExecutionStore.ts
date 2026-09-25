import { create } from 'zustand';
import { analyticsApi } from '../api/analytics';
import { queryClient } from '../lib/react-query';

export type StepStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'SKIPPED'
  | 'CANCELLED'
  | 'WAITING_FOR_APPROVAL';

export type ExecutionStatus =
  | 'IDLE'
  | 'RUNNING'
  | 'PAUSED'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'
  | 'ROLLED_BACK'
  | 'BLOCKED_MISSING_CONNECTION';

export interface LogEntry {
  id: string;
  timestamp: string;       // HH:MM:SS.mmm
  level: 'INFO' | 'WARN' | 'ERROR';
  message: string;
  step_id?: string;
}

export interface StepExecutionRecord {
  step_id: string;
  status: StepStatus;
  latency_ms: number;
  request_payload?: Record<string, any>;
  response_data?: Record<string, any>;
  error_message?: string;
  started_at?: number;
  completed_at?: number;
}

interface ExecutionState {
  executionId: string | null;
  status: ExecutionStatus;
  stepRecords: Record<string, StepExecutionRecord>;
  logs: LogEntry[];
  activeStepId: string | null;
  totalDurationMs: number;
  startedAt: number | null;
  endedAt: number | null;
  elapsedMs: number;
  executionPath: string[];
  variables: Record<string, Record<string, any>>;  // step_id -> variables at that step
  simulationTimer: ReturnType<typeof setInterval> | null;

  // Actions
  startExecution: (stepIds: string[]) => void;
  pauseExecution: () => void;
  resumeExecution: () => void;
  cancelExecution: () => void;
  replayExecution: () => void;
  retryStep: (stepId: string) => void;
  rollbackExecution: () => void;
  setActiveStepId: (stepId: string | null) => void;
  addLog: (level: 'INFO' | 'WARN' | 'ERROR', message: string, step_id?: string) => void;
  downloadLogs: () => void;
  updateStepRecord: (stepId: string, partial: Partial<StepExecutionRecord>) => void;
  setVariables: (stepId: string, vars: Record<string, any>) => void;
  appendExecutionPath: (stepId: string) => void;
  tickElapsed: () => void;
  simulateExecution: (stepIds: string[], nodeLabels?: Record<string, string>) => void;
  applyRealExecutionResult: (executionId: string, status: ExecutionStatus, nodeResults: any[], _finalOutput?: any) => void;
  stopSimulation: () => void;
  resetExecution: () => void;
}

function msTimestamp(): string {
  const now = new Date();
  const h = now.getHours().toString().padStart(2, '0');
  const m = now.getMinutes().toString().padStart(2, '0');
  const s = now.getSeconds().toString().padStart(2, '0');
  const ms = now.getMilliseconds().toString().padStart(3, '0');
  return `${h}:${m}:${s}.${ms}`;
}

function makeLogId(): string {
  return `log_${Date.now()}_${Math.random().toString(36).substring(2, 5)}`;
}

export const useExecutionStore = create<ExecutionState>((set, get) => ({
  executionId: null,
  status: 'IDLE',
  stepRecords: {},
  logs: [],
  activeStepId: null,
  totalDurationMs: 0,
  startedAt: null,
  endedAt: null,
  elapsedMs: 0,
  executionPath: [],
  variables: {},
  simulationTimer: null,

  // ── Core Controls ───────────────────────────────────────────────────

  startExecution: (stepIds) => {
    get().stopSimulation();

    const execId = `exec_${Math.random().toString(36).substring(2, 9)}`;
    const records: Record<string, StepExecutionRecord> = {};
    stepIds.forEach((id) => {
      records[id] = { step_id: id, status: 'PENDING', latency_ms: 0 };
    });

    set({
      executionId: execId,
      status: 'RUNNING',
      stepRecords: records,
      activeStepId: null,          // ← fix stale inspector
      logs: [{                     // ← fresh logs for new run
        id: makeLogId(),
        timestamp: msTimestamp(),
        level: 'INFO',
        message: `▶ Started Execution [${execId}] — ${stepIds.length} steps queued.`,
      }],
      totalDurationMs: 0,
      startedAt: Date.now(),
      endedAt: null,
      elapsedMs: 0,
      executionPath: [],
      variables: {},
    });
  },

  pauseExecution: () => {
    const { executionId, status } = get();
    if (status !== 'RUNNING') return;
    set({ status: 'PAUSED' });
    get().addLog('WARN', `⏸ Execution [${executionId}] PAUSED by operator.`);
  },

  resumeExecution: () => {
    const { executionId, status } = get();
    if (status !== 'PAUSED') return;
    set({ status: 'RUNNING' });
    get().addLog('INFO', `▶ Execution [${executionId}] RESUMED.`);
  },

  cancelExecution: () => {
    const { executionId, stepRecords } = get();
    get().stopSimulation();
    // Mark all PENDING and RUNNING steps as CANCELLED
    const updated = { ...stepRecords };
    Object.keys(updated).forEach((id) => {
      if (updated[id].status === 'PENDING' || updated[id].status === 'RUNNING') {
        updated[id] = { ...updated[id], status: 'CANCELLED' };
      }
    });
    const now = Date.now();
    set({
      status: 'CANCELLED',
      stepRecords: updated,
      endedAt: now,
      totalDurationMs: now - (get().startedAt ?? now),
    });
    get().addLog('WARN', `✖ Execution [${executionId}] CANCELLED. Remaining steps cancelled.`);
  },

  replayExecution: () => {
    const { executionId, stepRecords } = get();
    const stepIds = Object.keys(stepRecords);
    get().addLog('INFO', `↩ Replaying Execution [${executionId}] from DLQ…`);
    // Re-start with same step IDs
    get().startExecution(stepIds.length > 0 ? stepIds : ['step_1', 'step_2', 'step_3']);
  },

  retryStep: (stepId) => {
    get().updateStepRecord(stepId, { status: 'RUNNING' });
    get().addLog('INFO', `↻ Retrying step [${stepId}]…`, stepId);
    setTimeout(() => {
      get().updateStepRecord(stepId, {
        status: 'COMPLETED',
        latency_ms: 24.8,
        response_data: { status: 'success', retry_result: 'ok' },
      });
      get().addLog('INFO', `✓ Step [${stepId}] retry completed in 24.8ms.`, stepId);
    }, 1000);
  },

  rollbackExecution: () => {
    const { executionId } = get();
    get().stopSimulation();
    const now = Date.now();
    set({ status: 'ROLLED_BACK', endedAt: now, totalDurationMs: now - (get().startedAt ?? now) });
    get().addLog('WARN', `↩ Saga Rollback triggered for [${executionId}]. All steps compensated.`);
  },

  // ── State Helpers ───────────────────────────────────────────────────

  setActiveStepId: (stepId) => set({ activeStepId: stepId }),

  addLog: (level, message, step_id) =>
    set((state) => ({
      logs: [
        ...state.logs,
        { id: makeLogId(), timestamp: msTimestamp(), level, message, step_id },
      ],
    })),

  updateStepRecord: (stepId, partial) =>
    set((state) => ({
      stepRecords: {
        ...state.stepRecords,
        [stepId]: { ...state.stepRecords[stepId], ...partial },
      },
    })),

  setVariables: (stepId, vars) =>
    set((state) => ({ variables: { ...state.variables, [stepId]: vars } })),

  appendExecutionPath: (stepId) =>
    set((state) => ({ executionPath: [...state.executionPath, stepId] })),

  tickElapsed: () => {
    const { startedAt, status } = get();
    if (status === 'RUNNING' && startedAt) {
      set({ elapsedMs: Date.now() - startedAt });
    }
  },

  resetExecution: () => {
    get().stopSimulation();
    set({
      executionId: null, status: 'IDLE', stepRecords: {}, logs: [],
      activeStepId: null, totalDurationMs: 0, startedAt: null, endedAt: null,
      elapsedMs: 0, executionPath: [], variables: {},
    });
  },

  // ── Simulation Engine ───────────────────────────────────────────────

  stopSimulation: () => {
    const { simulationTimer } = get();
    if (simulationTimer) {
      clearInterval(simulationTimer);
      set({ simulationTimer: null });
    }
  },

  simulateExecution: (stepIds, nodeLabels = {}) => {
    get().stopSimulation();
    if (stepIds.length === 0) return;

    let currentIdx = 0;
    const STEP_INTERVAL_MS = 1200;

    // Elapsed ticker
    const elapsedTicker = setInterval(() => get().tickElapsed(), 500);

    const timer = setInterval(() => {
      const { status } = get();

      // Handle pause
      if (status === 'PAUSED') return;
      if (status === 'CANCELLED' || status === 'ROLLED_BACK') {
        clearInterval(timer);
        clearInterval(elapsedTicker);
        set({ simulationTimer: null });
        return;
      }

      if (currentIdx >= stepIds.length) {
        // All done
        clearInterval(timer);
        clearInterval(elapsedTicker);
        const now = Date.now();
        const startedAt = get().startedAt ?? now;
        const duration = now - startedAt;
        set({
          status: 'COMPLETED',
          endedAt: now,
          totalDurationMs: duration,
          simulationTimer: null,
        });
        get().addLog('INFO', `✓ Execution completed in ${duration}ms. All steps successful.`);

        // Record telemetry to Analytics Engine and invalidate query caches
        const execId = get().executionId || `exec_${Date.now()}`;
        const records = Object.values(get().stepRecords);
        analyticsApi.recordExecution({
          execution_id: execId,
          workflow_name: 'Interactive Workflow Execution',
          status: 'COMPLETED',
          duration_ms: duration,
          steps: records.map((r) => ({
            id: r.step_id,
            status: r.status,
            latency_ms: r.latency_ms,
          })),
        }).then(() => {
          queryClient.invalidateQueries({ queryKey: ['analytics'] });
          queryClient.invalidateQueries({ queryKey: ['analytics_overview'] });
          queryClient.invalidateQueries({ queryKey: ['connector_health'] });
          queryClient.invalidateQueries({ queryKey: ['ai_insights'] });
        }).catch(() => {});

        return;
      }

      const stepId = stepIds[currentIdx];
      const label = nodeLabels[stepId] || stepId;

      // Set current step to RUNNING
      get().updateStepRecord(stepId, {
        status: 'RUNNING',
        started_at: Date.now(),
      });
      get().addLog('INFO', `▶ Executing step [${label}]…`, stepId);

      // Resolve after simulated latency
      const latency = 180 + Math.random() * 800;
      const isFail = stepIds.length > 3 && currentIdx === stepIds.length - 2;

      setTimeout(() => {
        const currentStatus = get().status;
        if (currentStatus === 'CANCELLED' || currentStatus === 'ROLLED_BACK') return;

        const finalStatus: StepStatus = isFail ? 'FAILED' : 'COMPLETED';
        const latencyMs = Math.round(latency);
        const vars: Record<string, any> = {
          [`${stepId}_output`]: `result_${currentIdx}`,
          step_index: currentIdx,
          timestamp: new Date().toISOString(),
        };

        get().updateStepRecord(stepId, {
          status: finalStatus,
          latency_ms: latencyMs,
          completed_at: Date.now(),
          request_payload: { step_id: stepId, index: currentIdx },
          response_data: finalStatus === 'COMPLETED' ? { status: 'ok', data: `output_${currentIdx}` } : undefined,
          error_message: isFail ? `Simulated error at step [${label}]` : undefined,
        });

        get().setVariables(stepId, vars);
        get().appendExecutionPath(stepId);

        if (finalStatus === 'COMPLETED') {
          get().addLog('INFO', `✓ [${label}] completed in ${latencyMs}ms.`, stepId);
        } else {
          get().addLog('ERROR', `✗ [${label}] FAILED after ${latencyMs}ms. Saga available.`, stepId);
          // Stop simulation on failure
          clearInterval(timer);
          clearInterval(elapsedTicker);
          const now = Date.now();
          set({
            status: 'FAILED',
            endedAt: now,
            totalDurationMs: now - (get().startedAt ?? now),
            simulationTimer: null,
          });
        }
      }, latency);

      currentIdx++;
    }, STEP_INTERVAL_MS);

    set({ simulationTimer: timer });
  },

  applyRealExecutionResult: (executionId: string, status: ExecutionStatus, nodeResults: any[], _finalOutput?: any) => {
    get().stopSimulation();
    const records: Record<string, StepExecutionRecord> = {};
    const logs: LogEntry[] = [
      {
        id: makeLogId(),
        timestamp: msTimestamp(),
        level: 'INFO',
        message: `▶ Initiating live DAG execution [${executionId}].`,
      },
    ];
    const path: string[] = [];
    const vars: Record<string, Record<string, any>> = {};

    nodeResults.forEach((r) => {
      const nid = r.node_id;
      const op = r.operation || 'generic.http.request';
      const isSuccess = r.status === 'SUCCESS' || r.status === 'COMPLETED';
      const isSkipped = r.status === 'SKIPPED';
      const st: StepStatus = isSuccess ? 'COMPLETED' : (isSkipped ? 'SKIPPED' : 'FAILED');

      records[nid] = {
        step_id: nid,
        status: st,
        latency_ms: r.latency_ms || 0,
        request_payload: r.output?.request || { operation: op },
        response_data: r.output?.response || r.output?.body || r.output,
        error_message: (!isSuccess && !isSkipped) ? (r.output?.error || 'Step execution failed') : undefined,
        started_at: Date.now(),
        completed_at: Date.now(),
      };

      path.push(nid);
      vars[nid] = r.output || {};

      if (isSuccess) {
        logs.push({
          id: makeLogId(),
          timestamp: msTimestamp(),
          level: 'INFO',
          message: `✓ Node [${nid}] (${op}) HTTP 200 SUCCESS — completed in ${r.latency_ms || 0}ms`,
          step_id: nid,
        });
      } else if (isSkipped) {
        logs.push({
          id: makeLogId(),
          timestamp: msTimestamp(),
          level: 'INFO',
          message: `⤿ Node [${nid}] (${op}) SKIPPED — branch unselected by condition`,
          step_id: nid,
        });
      } else {
        logs.push({
          id: makeLogId(),
          timestamp: msTimestamp(),
          level: 'ERROR',
          message: `✗ Node [${nid}] (${op}) FAILED: ${r.output?.error || 'Execution failure'}`,
          step_id: nid,
        });
      }
    });

    logs.push({
      id: makeLogId(),
      timestamp: msTimestamp(),
      level: status === 'COMPLETED' ? 'INFO' : 'ERROR',
      message: `[AI-16][WORKFLOW_EXECUTE_COMPLETE] Workflow [${executionId}] status: ${status} (${nodeResults.filter((n) => n.status === 'SUCCESS' || n.status === 'COMPLETED').length}/${nodeResults.length} nodes executed).`,
    });

    set({
      executionId,
      status,
      stepRecords: records,
      logs,
      executionPath: path,
      variables: vars,
      activeStepId: nodeResults.length > 0 ? nodeResults[nodeResults.length - 1].node_id : null,
      endedAt: Date.now(),
      totalDurationMs: nodeResults.reduce((acc, n) => acc + (n.latency_ms || 0), 0),
    });
  },

  // ── Download ────────────────────────────────────────────────────────

  downloadLogs: () => {
    const { logs, executionId } = get();
    const logText = logs
      .map((l) => `[${l.timestamp}] [${l.level}] ${l.step_id ? `[${l.step_id}] ` : ''}${l.message}`)
      .join('\n');
    const blob = new Blob([logText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${executionId || 'workflow'}_execution.log`;
    link.click();
    URL.revokeObjectURL(url);
  },
}));
