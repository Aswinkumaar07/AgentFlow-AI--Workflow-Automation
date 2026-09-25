import React, { useEffect, useState } from 'react';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import { useExecutionStore } from '../../store/useExecutionStore';
import { workflowApi } from '../../api/workflows';
import { PlayCircle, X, CheckCircle2, AlertCircle, Clock, PauseCircle, ChevronRight } from 'lucide-react';

export const ExecutionHistoryModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onSelectExecution: (executionResult: any) => void;
}> = ({ isOpen, onClose, onSelectExecution }) => {
  const { workflowId } = useWorkflowStore();
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      workflowApi
        .getExecutions(workflowId)
        .then((res) => setExecutions(res))
        .catch(() => setExecutions([]))
        .finally(() => setLoading(false));
    }
  }, [isOpen, workflowId]);

  if (!isOpen) return null;

  const handleInspect = (item: any) => {
    const isOk = item.status === 'COMPLETED';
    const isWaiting = item.status === 'WAITING' || item.status === 'WAITING_FOR_APPROVAL' || item.status === 'PAUSED';

    const nodesExecuted = item.node_records ? Object.keys(item.node_records).length : (item.nodes_executed || 0);
    const nodeResultsList = item.node_records
      ? Object.entries(item.node_records).map(([nid, rec]: [string, any]) => ({
          node_id: nid,
          operation: rec.operation || 'generic.http.request',
          status: rec.status || 'SUCCESS',
          output: rec.output || {},
          latency_ms: rec.latency || 0,
          retries: rec.retries || 0,
        }))
      : [];

    const telemetryPayload = {
      ok: isOk,
      message: isOk
        ? `✓ Workflow [${item.execution_id}] COMPLETED`
        : isWaiting
        ? `⏸ Workflow [${item.execution_id}] ${item.status}`
        : `✕ Workflow [${item.execution_id}] ${item.status || 'FAILED'}`,
      execution_id: item.execution_id,
      workflow_id: item.workflow_id || workflowId,
      version_id: item.version_id,
      version_number: item.version_number,
      status: item.status,
      nodes_executed: nodesExecuted,
      node_results: nodeResultsList,
      can_resume: Boolean(item.can_resume || isWaiting),
    };

    useExecutionStore.getState().applyRealExecutionResult(
      item.execution_id,
      item.status || 'COMPLETED',
      nodeResultsList,
      {}
    );

    onSelectExecution(telemetryPayload);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-[#13102A]/95 border border-[rgba(255,255,255,0.12)] rounded-2xl shadow-2xl backdrop-blur-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 border-b border-[rgba(255,255,255,0.10)] flex items-center justify-between bg-[#1B1728]/50">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center font-bold">
              <PlayCircle className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">Execution History</h3>
              <p className="text-[10px] text-[#A098AE]">Historical telemetry & node output snapshots</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Executions List */}
        <div className="p-4 flex-1 overflow-y-auto space-y-2.5 scrollbar-thin scrollbar-thumb-[#231E3A]">
          {loading ? (
            <p className="text-xs text-center text-[#A098AE] py-10 font-mono">Loading execution history…</p>
          ) : executions.length === 0 ? (
            <div className="text-center py-10 space-y-2">
              <Clock className="h-8 w-8 text-[#A098AE]/40 mx-auto" />
              <p className="text-xs text-[#A098AE] font-semibold">No execution history recorded yet.</p>
              <p className="text-[11px] text-[#7A748E]">
                Click <span className="text-[#FF6D00] font-bold">Execute</span> to run your workflow and record execution history.
              </p>
            </div>
          ) : (
            executions.map((item) => {
              const isCompleted = item.status === 'COMPLETED';
              const isWaiting = item.status === 'WAITING' || item.status === 'WAITING_FOR_APPROVAL' || item.status === 'PAUSED';
              const verNum = item.version_number ? `v${item.version_number}` : (item.version_id || 'v1');
              const nodeCount = item.node_records ? Object.keys(item.node_records).length : (item.node_count || 0);
              const startTimeFormatted = item.start_time ? new Date(item.start_time * 1000).toLocaleString() : 'Just now';

              return (
                <div
                  key={item.execution_id}
                  onClick={() => handleInspect(item)}
                  className="p-4 rounded-xl border border-[rgba(255,255,255,0.08)] bg-[#13102A]/80 hover:border-[#FF6D00]/50 hover:bg-[#1B1728] transition cursor-pointer flex items-center justify-between group"
                >
                  <div className="flex items-center gap-3">
                    {/* Status Icon */}
                    <div>
                      {isCompleted ? (
                        <div className="w-8 h-8 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center">
                          <CheckCircle2 className="h-4 w-4" />
                        </div>
                      ) : isWaiting ? (
                        <div className="w-8 h-8 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center">
                          <PauseCircle className="h-4 w-4" />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 flex items-center justify-center">
                          <AlertCircle className="h-4 w-4" />
                        </div>
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white font-mono">{item.execution_id}</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30 font-mono">
                          Version: {verNum}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase font-mono ${
                            isCompleted
                              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                              : isWaiting
                              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                              : 'bg-red-500/15 text-red-400 border border-red-500/30'
                          }`}
                        >
                          {item.status || 'COMPLETED'}
                        </span>
                      </div>
                      <p className="text-[11px] text-[#A098AE] font-mono">
                        Executed: {startTimeFormatted} • {nodeCount} node{nodeCount === 1 ? '' : 's'} recorded
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1 text-xs font-bold text-[#FF6D00] opacity-80 group-hover:opacity-100 transition">
                    <span>Inspect</span>
                    <ChevronRight className="h-4 w-4" />
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
