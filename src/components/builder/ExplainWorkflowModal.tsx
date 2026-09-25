import React from 'react';
import { BookOpen, X, Clock, DollarSign, Cpu, AlertTriangle, Lightbulb, CheckCircle2 } from 'lucide-react';

export interface ExplanationData {
  summary: string;
  step_explanations: Array<{
    step_id: string;
    label: string;
    provider: string;
    operation: string;
    explanation: string;
  }>;
  variables_used: string[];
  dependencies: string[];
  execution_order: string[];
  estimated_runtime_ms: number;
  estimated_cost_usd: number;
  potential_failures: string[];
  optimization_suggestions: string[];
  markdown_report: string;
}

interface ExplainWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  explanation: ExplanationData | null;
}

export const ExplainWorkflowModal: React.FC<ExplainWorkflowModalProps> = ({
  isOpen,
  onClose,
  explanation,
}) => {
  if (!isOpen || !explanation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              AI Workflow Explanation & Insights
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Summary Box */}
          <div className="p-4 bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/50 rounded-lg">
            <h4 className="text-sm font-semibold text-indigo-900 dark:text-indigo-200 mb-1">
              Workflow Overview
            </h4>
            <p className="text-xs text-indigo-800 dark:text-indigo-300 leading-relaxed">
              {explanation.summary}
            </p>
          </div>

          {/* Telemetry Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 rounded-lg flex items-center space-x-3">
              <Clock className="w-5 h-5 text-emerald-500 shrink-0" />
              <div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">Est. Runtime</div>
                <div className="text-sm font-bold text-slate-900 dark:text-white">{explanation.estimated_runtime_ms} ms</div>
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 rounded-lg flex items-center space-x-3">
              <DollarSign className="w-5 h-5 text-blue-500 shrink-0" />
              <div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">Est. Cost</div>
                <div className="text-sm font-bold text-slate-900 dark:text-white">${explanation.estimated_cost_usd}</div>
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 rounded-lg flex items-center space-x-3">
              <Cpu className="w-5 h-5 text-purple-500 shrink-0" />
              <div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">Total Steps</div>
                <div className="text-sm font-bold text-slate-900 dark:text-white">{explanation.step_explanations.length} Steps</div>
              </div>
            </div>
          </div>

          {/* Step Breakdown */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-indigo-500" />
              <span>Step-by-Step Execution Breakdown</span>
            </h4>
            <div className="space-y-2">
              {explanation.step_explanations.map((step, idx) => (
                <div
                  key={step.step_id}
                  className="p-3 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-lg text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-900 dark:text-white">
                      Step {idx + 1}: {step.label}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-300">
                      {step.provider} ({step.operation})
                    </span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-300">{step.explanation}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Potential Failures & Optimizations */}
          <div className="grid grid-cols-2 gap-4">
            {explanation.potential_failures.length > 0 && (
              <div className="p-4 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 rounded-lg space-y-2">
                <h5 className="text-xs font-semibold text-amber-900 dark:text-amber-300 flex items-center space-x-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  <span>Potential Failures</span>
                </h5>
                <ul className="text-xs text-amber-800 dark:text-amber-400 space-y-1 list-disc list-inside">
                  {explanation.potential_failures.map((pf, i) => (
                    <li key={i}>{pf}</li>
                  ))}
                </ul>
              </div>
            )}

            {explanation.optimization_suggestions.length > 0 && (
              <div className="p-4 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/40 rounded-lg space-y-2">
                <h5 className="text-xs font-semibold text-emerald-900 dark:text-emerald-300 flex items-center space-x-1.5">
                  <Lightbulb className="w-4 h-4 text-emerald-500" />
                  <span>Optimization Suggestions</span>
                </h5>
                <ul className="text-xs text-emerald-800 dark:text-emerald-400 space-y-1 list-disc list-inside">
                  {explanation.optimization_suggestions.map((opt, i) => (
                    <li key={i}>{opt}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
