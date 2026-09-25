import React, { useState } from 'react';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { ExecutionControls } from '../components/execution/ExecutionControls';
import { ExecutionTimeline } from '../components/execution/ExecutionTimeline';
import { LiveLogsPanel } from '../components/execution/LiveLogsPanel';
import { PayloadInspectorModal } from '../components/execution/PayloadInspectorModal';
import { ExecutionCanvasOverlay } from '../components/execution/ExecutionCanvasOverlay';
import { WorkflowCanvas } from '../components/builder/WorkflowCanvas';
import { useExecutionStore } from '../store/useExecutionStore';
import { useWorkflowStore } from '../store/useWorkflowStore';
import { useExecutionWebSocket } from '../hooks/useExecutionWebSocket';
import { Zap, AlertTriangle } from 'lucide-react';

/**
 * Inner component — needs access to React Flow viewport via useReactFlow.
 * ExecutionStudioPage wraps this so the ReactFlowProvider from WorkflowCanvas
 * is available before we try to read the transform.
 */
const ExecutionStudioInner: React.FC = () => {
  const { nodes } = useWorkflowStore();
  const { executionId, status } = useExecutionStore();
  const [rfTransform, setRfTransform] = useState('translate(0px, 0px) scale(1)');

  // WebSocket — enabled only when execution is active
  const nodeIds = nodes.map((n) => n.id);
  useExecutionWebSocket(executionId, nodeIds, status !== 'IDLE');

  const isIdle = status === 'IDLE';
  const hasWorkflow = nodes.length > 0;

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] border border-border rounded-2xl overflow-hidden bg-background shadow-xl">

      {/* ── Top Control Bar ── */}
      <ExecutionControls />

      {/* ── Body ── */}
      <div className="flex-1 flex overflow-hidden min-h-0">

        {/* Timeline Sidebar */}
        <ExecutionTimeline />

        {/* Main Canvas + Logs area */}
        <div className="flex-1 flex flex-col h-full min-w-0 relative">

          {/* Canvas + Overlay */}
          <div className="flex-1 relative overflow-hidden">
            {/* Empty state */}
            {!hasWorkflow && isIdle && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 z-20 pointer-events-none">
                <div className="h-16 w-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
                  <Zap className="h-8 w-8" />
                </div>
                <div className="text-center max-w-xs">
                  <p className="font-bold text-foreground text-base">No Workflow Loaded</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Go to the Workflow Builder, generate or design a workflow, then return here to execute it.
                  </p>
                </div>
              </div>
            )}

            {/* WorkflowCanvas in read-only execution mode */}
            <WorkflowCanvas
              readOnly
              onViewportChange={(vp) => {
                setRfTransform(
                  `translate(${vp.x}px, ${vp.y}px) scale(${vp.zoom})`
                );
              }}
            />

            {/* Animated node status overlays */}
            {!isIdle && (
              <ExecutionCanvasOverlay
                nodes={nodes}
                transform={rfTransform}
              />
            )}

            {/* Paused banner */}
            {status === 'PAUSED' && (
              <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 px-4 py-2 bg-amber-500/90 text-white text-xs font-bold rounded-xl shadow-lg backdrop-blur-sm">
                <AlertTriangle className="h-4 w-4" /> Execution Paused — click Resume to continue
              </div>
            )}

            {/* Cancelled banner */}
            {status === 'CANCELLED' && (
              <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 px-4 py-2 bg-slate-600/90 text-white text-xs font-bold rounded-xl shadow-lg backdrop-blur-sm">
                Execution Cancelled — Start a new run
              </div>
            )}

            {/* Rolled back banner */}
            {status === 'ROLLED_BACK' && (
              <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 px-4 py-2 bg-purple-600/90 text-white text-xs font-bold rounded-xl shadow-lg backdrop-blur-sm">
                Saga Rollback Complete — all steps compensated
              </div>
            )}
          </div>

          {/* Live Logs Panel (resizable) */}
          <LiveLogsPanel />
        </div>
      </div>

      {/* Step Payload Inspector (modal) */}
      <PayloadInspectorModal />
    </div>
  );
};

export const ExecutionStudioPage: React.FC = () => (
  <DashboardLayout>
    <ExecutionStudioInner />
  </DashboardLayout>
);
