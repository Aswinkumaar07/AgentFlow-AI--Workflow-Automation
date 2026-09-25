import React, { useState } from 'react';
import { useExecutionStore } from '../../store/useExecutionStore';
import {
  Code2, X, CheckCircle2, AlertCircle, Copy,
  Variable, GitBranch, ChevronUp, Timer,
} from 'lucide-react';

type InspectorTab = 'payload' | 'variables' | 'path';

function formatLatency(ms: number): string {
  if (!ms) return '—';
  if (ms < 100)  return `${ms}ms`;
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function latencyColor(ms: number): string {
  if (!ms) return 'text-muted-foreground';
  if (ms < 100)  return 'text-emerald-500';
  if (ms < 1000) return 'text-amber-500';
  return 'text-rose-500';
}

function JSONBlock({ data, label }: { data: unknown; label: string }) {
  const [copied, setCopied] = useState(false);
  const json = JSON.stringify(data, null, 2);

  const copy = () => {
    navigator.clipboard?.writeText(json).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <h4 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{label}</h4>
        <button
          onClick={copy}
          className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition"
        >
          {copied
            ? <><ChevronUp className="h-3 w-3 text-emerald-500" /> Copied</>
            : <><Copy className="h-3 w-3" /> Copy</>
          }
        </button>
      </div>
      <div className="relative">
        <pre className="p-3 bg-muted/30 rounded-xl font-mono text-[11px] overflow-x-auto border border-border leading-relaxed whitespace-pre-wrap break-words max-h-48 overflow-y-auto">
          {data != null ? json : <span className="text-muted-foreground italic">null</span>}
        </pre>
      </div>
    </div>
  );
}

export const PayloadInspectorModal: React.FC = () => {
  const { activeStepId, setActiveStepId, stepRecords, variables, executionPath } = useExecutionStore();
  const [activeTab, setActiveTab] = useState<InspectorTab>('payload');

  if (!activeStepId) return null;

  const record = stepRecords[activeStepId];
  const stepVars = variables[activeStepId] ?? {};
  const stepIdx = executionPath.indexOf(activeStepId);
  const pathToStep = stepIdx >= 0 ? executionPath.slice(0, stepIdx + 1) : executionPath;

  const isFailed = record?.status === 'FAILED';
  const isCompleted = record?.status === 'COMPLETED';

  const tabs = [
    { id: 'payload' as InspectorTab, label: 'Payload', icon: Code2 },
    { id: 'variables' as InspectorTab, label: 'Variables', icon: Variable },
    { id: 'path' as InspectorTab, label: 'Exec Path', icon: GitBranch },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">

        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between bg-muted/20">
          <div className="flex items-center gap-2 min-w-0">
            <Code2 className="h-5 w-5 text-primary shrink-0" />
            <h3 className="font-bold text-sm">Step Telemetry Inspector</h3>
            <span className="font-mono text-[11px] bg-primary/10 text-primary px-2 py-0.5 rounded font-bold truncate">
              [{activeStepId}]
            </span>
          </div>
          <button
            onClick={() => setActiveStepId(null)}
            className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground shrink-0"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Status Summary Bar */}
        <div className="px-4 py-2.5 border-b border-border bg-muted/10 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            {isFailed
              ? <AlertCircle className="h-4 w-4 text-rose-500" />
              : <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            }
            <span className={`text-xs font-bold ${isFailed ? 'text-rose-500' : isCompleted ? 'text-emerald-500' : 'text-muted-foreground'}`}>
              {record?.status ?? 'PENDING'}
            </span>
          </div>

          <div className="flex items-center gap-3 text-[11px]">
            <span className={`flex items-center gap-1 font-mono font-bold ${latencyColor(record?.latency_ms ?? 0)}`}>
              <Timer className="h-3 w-3" />
              {formatLatency(record?.latency_ms ?? 0)}
              <span className={`text-[9px] px-1 py-0.5 rounded font-bold ml-1 ${
                (record?.latency_ms ?? 0) < 100  ? 'bg-emerald-500/10 text-emerald-500' :
                (record?.latency_ms ?? 0) < 1000 ? 'bg-amber-500/10 text-amber-500' :
                'bg-rose-500/10 text-rose-500'
              }`}>
                {(record?.latency_ms ?? 0) < 100 ? 'FAST' : (record?.latency_ms ?? 0) < 1000 ? 'OK' : 'SLOW'}
              </span>
            </span>
            <span className="text-muted-foreground font-mono">
              Path position: {stepIdx >= 0 ? `#${stepIdx + 1}` : 'Not executed'}
            </span>
          </div>
        </div>

        {/* Error message for failed steps */}
        {isFailed && record?.error_message && (
          <div className="px-4 py-2 bg-rose-500/10 border-b border-rose-500/20 text-xs text-rose-400 flex items-start gap-2">
            <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
            <span className="break-all">{record.error_message}</span>
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-border bg-muted/10">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-semibold border-b-2 transition ${
                activeTab === id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
              {id === 'variables' && Object.keys(stepVars).length > 0 && (
                <span className="text-[9px] bg-primary/20 text-primary px-1 rounded font-bold">
                  {Object.keys(stepVars).length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4">

          {/* ── Payload Tab ── */}
          {activeTab === 'payload' && (
            <>
              <JSONBlock
                label="Request Payload / Parameters"
                data={record?.request_payload ?? null}
              />
              <JSONBlock
                label="Response Output Data"
                data={record?.response_data ?? null}
              />
            </>
          )}

          {/* ── Variables Tab ── */}
          {activeTab === 'variables' && (
            <>
              {Object.keys(stepVars).length === 0 ? (
                <div className="text-center text-muted-foreground text-xs py-8">
                  No variables captured for this step.
                  {record?.status === 'PENDING' && ' Variables populate once the step executes.'}
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-[10px] text-muted-foreground">
                    Variables resolved at the time this step completed:
                  </p>
                  <div className="space-y-1.5">
                    {Object.entries(stepVars).map(([key, value]) => (
                      <div key={key} className="flex items-start gap-3 p-2.5 rounded-xl border border-border bg-muted/20">
                        <div className="flex items-center gap-1.5 shrink-0">
                          <Variable className="h-3 w-3 text-primary" />
                          <span className="font-mono text-xs font-bold text-primary">{key}</span>
                        </div>
                        <span className="font-mono text-xs text-foreground break-all">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                        <button
                          onClick={() => navigator.clipboard?.writeText(`{{${key}}}`)}
                          className="ml-auto shrink-0 text-[10px] text-muted-foreground hover:text-foreground transition"
                          title={`Copy {{${key}}} expression`}
                        >
                          <Copy className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                  <JSONBlock label="Full Variables Snapshot" data={stepVars} />
                </div>
              )}
            </>
          )}

          {/* ── Execution Path Tab ── */}
          {activeTab === 'path' && (
            <>
              {pathToStep.length === 0 ? (
                <div className="text-center text-muted-foreground text-xs py-8">
                  Execution path not yet recorded. Start a run to trace the DAG traversal.
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-[10px] text-muted-foreground">
                    Topological path traversed to reach <span className="text-primary font-bold">[{activeStepId}]</span>:
                  </p>
                  <div className="space-y-1">
                    {pathToStep.map((stepId, idx) => {
                      const isCurrent = stepId === activeStepId;
                      return (
                        <div key={stepId} className="flex items-center gap-2">
                          <div className={`flex items-center gap-2 flex-1 p-2 rounded-lg border transition ${
                            isCurrent ? 'border-primary/40 bg-primary/5' : 'border-border bg-muted/20'
                          }`}>
                            <span className={`h-5 w-5 rounded-full text-[10px] font-bold flex items-center justify-center shrink-0 ${
                              isCurrent ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                            }`}>
                              {idx + 1}
                            </span>
                            <span className={`font-mono text-xs ${isCurrent ? 'text-primary font-bold' : 'text-foreground'}`}>
                              {stepId}
                            </span>
                            {isCurrent && (
                              <span className="ml-auto text-[9px] text-primary font-bold bg-primary/10 px-1.5 py-0.5 rounded">
                                CURRENT
                              </span>
                            )}
                          </div>
                          {idx < pathToStep.length - 1 && (
                            <div className="h-4 w-px bg-border mx-2" />
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
