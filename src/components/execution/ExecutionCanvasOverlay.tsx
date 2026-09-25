import React, { useMemo } from 'react';
import { useExecutionStore, type StepStatus } from '../../store/useExecutionStore';
import type { Node } from '@xyflow/react';
import { CheckCircle2, AlertCircle, Loader2, Clock, Square, SkipForward } from 'lucide-react';

interface ExecutionCanvasOverlayProps {
  nodes: Node[];
  /** The CSS transform string from React Flow's viewport (translate + scale) */
  transform: string;
}

const STATUS_OVERLAY: Record<StepStatus, {
  ring: string;
  bg: string;
  icon: React.ReactNode;
  pulse: boolean;
  label: string;
}> = {
  PENDING:              { ring: 'ring-muted-foreground/20', bg: 'bg-muted/60',        icon: <Clock className="h-3 w-3" />,                    pulse: false, label: '' },
  RUNNING:              { ring: 'ring-blue-500/60',         bg: 'bg-blue-500/20',     icon: <Loader2 className="h-3 w-3 animate-spin" />,     pulse: true,  label: 'RUNNING' },
  COMPLETED:            { ring: 'ring-emerald-500/50',      bg: 'bg-emerald-500/15',  icon: <CheckCircle2 className="h-3 w-3" />,              pulse: false, label: '✓' },
  FAILED:               { ring: 'ring-rose-500/60',         bg: 'bg-rose-500/20',     icon: <AlertCircle className="h-3 w-3" />,               pulse: false, label: 'FAILED' },
  SKIPPED:              { ring: 'ring-slate-400/30',        bg: 'bg-slate-400/10',    icon: <SkipForward className="h-3 w-3" />,               pulse: false, label: 'SKIP' },
  CANCELLED:            { ring: 'ring-slate-400/30',        bg: 'bg-slate-400/10',    icon: <Square className="h-3 w-3" />,                   pulse: false, label: 'CANCELLED' },
  WAITING_FOR_APPROVAL: { ring: 'ring-amber-500/50',        bg: 'bg-amber-500/15',    icon: <Clock className="h-3 w-3" />,                    pulse: true,  label: 'WAITING' },
};

const OVERLAY_COLORS: Record<StepStatus, string> = {
  PENDING:              'border-transparent',
  RUNNING:              'border-blue-500 shadow-blue-500/30 shadow-lg',
  COMPLETED:            'border-emerald-500 shadow-emerald-500/20 shadow-md',
  FAILED:               'border-rose-500 shadow-rose-500/30 shadow-lg',
  SKIPPED:              'border-slate-400',
  CANCELLED:            'border-slate-400/50',
  WAITING_FOR_APPROVAL: 'border-amber-500 shadow-amber-500/30 shadow-md',
};

/**
 * ExecutionCanvasOverlay
 * Renders absolutely positioned status badges on top of each canvas node,
 * synchronized with the React Flow viewport transform so they track node positions.
 */
export const ExecutionCanvasOverlay: React.FC<ExecutionCanvasOverlayProps> = ({ nodes, transform }) => {
  const { stepRecords, status: execStatus } = useExecutionStore();

  // Only render overlays when executing
  const shouldRender = execStatus !== 'IDLE';

  const overlays = useMemo(() => {
    if (!shouldRender) return [];
    return nodes.map((node) => {
      const rec = stepRecords[node.id];
      const stepStatus: StepStatus = rec?.status ?? 'PENDING';
      const cfg = STATUS_OVERLAY[stepStatus];
      return { node, stepStatus, cfg, rec };
    });
  }, [nodes, stepRecords, shouldRender]);

  if (!shouldRender || overlays.length === 0) return null;

  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden"
      style={{ zIndex: 10 }}
      aria-hidden="true"
    >
      {/* Transform wrapper mirrors React Flow viewport */}
      <div style={{ transform, transformOrigin: '0 0', position: 'absolute', top: 0, left: 0 }}>
        {overlays.map(({ node, stepStatus, cfg, rec }) => {
          const NODE_W = 220;
          const NODE_H = 72;

          return (
            <div
              key={node.id}
              style={{
                position: 'absolute',
                left: node.position.x,
                top: node.position.y,
                width: NODE_W,
                height: NODE_H,
              }}
            >
              {/* Node border overlay */}
              <div
                className={`absolute inset-0 rounded-2xl border-2 transition-all duration-300 pointer-events-none ${OVERLAY_COLORS[stepStatus]}`}
              />

              {/* Pulsing glow for RUNNING and WAITING */}
              {cfg.pulse && (
                <div
                  className={`absolute inset-0 rounded-2xl opacity-40 ${cfg.bg} animate-ping`}
                  style={{ animationDuration: '1.5s' }}
                />
              )}

              {/* Status badge — top right corner */}
              {stepStatus !== 'PENDING' && (
                <div
                  className={`absolute -top-2 -right-2 flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ring-2 ${cfg.ring} ${cfg.bg}
                    ${stepStatus === 'RUNNING'   ? 'text-blue-400 border-blue-500/50' :
                      stepStatus === 'COMPLETED' ? 'text-emerald-400 border-emerald-500/40' :
                      stepStatus === 'FAILED'    ? 'text-rose-400 border-rose-500/50' :
                      stepStatus === 'WAITING_FOR_APPROVAL' ? 'text-amber-400 border-amber-500/40' :
                      'text-slate-400 border-slate-400/30'}
                  `}
                >
                  {cfg.icon}
                  {cfg.label && <span>{cfg.label}</span>}
                </div>
              )}

              {/* Latency badge — bottom right */}
              {rec?.latency_ms ? (
                <div className={`absolute -bottom-2 -right-2 text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full border ${
                  rec.latency_ms > 1000 ? 'bg-rose-500/10 text-rose-400 border-rose-500/30' :
                  rec.latency_ms > 500  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
                  'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                }`}>
                  {rec.latency_ms < 1000 ? `${rec.latency_ms}ms` : `${(rec.latency_ms / 1000).toFixed(1)}s`}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
};
