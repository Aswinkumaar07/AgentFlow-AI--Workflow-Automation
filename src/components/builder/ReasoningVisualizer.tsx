import React from 'react';
import { Cpu, CheckCircle2, Clock, DollarSign, ShieldCheck, X, FileText } from 'lucide-react';

export interface ReasoningStageItem {
  id: string;
  label: string;
}

interface ReasoningVisualizerProps {
  isOpen: boolean;
  onCancel: () => void;
  currentStage: string;
  progressPercentage: number;
  confidence?: number;
  estimatedRuntimeMs?: number;
  estimatedCostUsd?: number;
  reasoningSummary?: string;
  isCompleted?: boolean;
}

export const ReasoningVisualizer: React.FC<ReasoningVisualizerProps> = ({
  isOpen,
  onCancel,
  currentStage,
  progressPercentage,
  confidence = 0.95,
  estimatedRuntimeMs = 1200,
  estimatedCostUsd = 0.0004,
  reasoningSummary,
  isCompleted = false,
}) => {
  if (!isOpen) return null;

  const STAGES: ReasoningStageItem[] = [
    { id: 'intent', label: 'Understanding Intent...' },
    { id: 'connectors', label: 'Finding Connectors...' },
    { id: 'apis', label: 'Finding APIs...' },
    { id: 'dag', label: 'Building DAG...' },
    { id: 'variables', label: 'Generating Variables...' },
    { id: 'validating', label: 'Validating...' },
    { id: 'optimizing', label: 'Optimizing...' },
    { id: 'completed', label: 'Completed' },
  ];

  const currentStageIdx = STAGES.findIndex((s) => s.id === currentStage);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-xl p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md">
              <Cpu className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">AI Live Reasoning Engine</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Synthesizing & Validating Execution Graph</p>
            </div>
          </div>
          {!isCompleted && (
            <button
              onClick={onCancel}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              title="Cancel generation"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
            <span>{isCompleted ? 'Completed' : STAGES[Math.max(0, currentStageIdx)]?.label || 'Processing...'}</span>
            <span>{progressPercentage}%</span>
          </div>
          <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 transition-all duration-300 rounded-full"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Live Reasoning Stages Stepper */}
        <div className="space-y-2 max-h-48 overflow-y-auto p-1">
          {STAGES.map((stg, idx) => {
            const isDone = currentStageIdx > idx || isCompleted;
            const isCurrent = currentStageIdx === idx && !isCompleted;

            return (
              <div
                key={stg.id}
                className={`flex items-center justify-between p-2.5 rounded-lg text-xs transition ${
                  isCurrent
                    ? 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-semibold border border-indigo-200 dark:border-indigo-800'
                    : isDone
                    ? 'text-slate-600 dark:text-slate-400'
                    : 'text-slate-400 dark:text-slate-600 opacity-60'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  ) : isCurrent ? (
                    <Cpu className="w-4 h-4 text-indigo-500 animate-spin shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-300 dark:border-slate-700 shrink-0" />
                  )}
                  <span>{stg.label}</span>
                </div>
                {isDone && <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400">DONE</span>}
              </div>
            );
          })}
        </div>

        {/* Reasoning Summary */}
        {reasoningSummary && (
          <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg text-xs text-slate-600 dark:text-slate-300 space-y-1">
            <div className="font-semibold flex items-center space-x-1 text-slate-800 dark:text-slate-200">
              <FileText className="w-3.5 h-3.5 text-indigo-500" />
              <span>Reasoning Summary</span>
            </div>
            <p className="font-mono text-[11px] leading-relaxed truncate">{reasoningSummary}</p>
          </div>
        )}

        {/* Telemetry Footer Card */}
        {isCompleted && (
          <div className="grid grid-cols-3 gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-lg flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-indigo-500" />
              <div>
                <div className="text-[10px] text-slate-400">Confidence</div>
                <div className="text-xs font-bold text-slate-900 dark:text-white">{(confidence * 100).toFixed(0)}%</div>
              </div>
            </div>

            <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-lg flex items-center space-x-2">
              <Clock className="w-4 h-4 text-emerald-500" />
              <div>
                <div className="text-[10px] text-slate-400">Est. Time</div>
                <div className="text-xs font-bold text-slate-900 dark:text-white">{estimatedRuntimeMs} ms</div>
              </div>
            </div>

            <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-lg flex items-center space-x-2">
              <DollarSign className="w-4 h-4 text-blue-500" />
              <div>
                <div className="text-[10px] text-slate-400">Est. Cost</div>
                <div className="text-xs font-bold text-slate-900 dark:text-white">${estimatedCostUsd}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
