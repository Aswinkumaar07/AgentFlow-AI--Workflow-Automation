import React from 'react';
import { Zap, X, TrendingUp, DollarSign, Sparkles } from 'lucide-react';

export interface SuggestionItem {
  id: string;
  category: string;
  title: string;
  description: string;
  impact: string;
}

export interface OptimizerData {
  performance_score: number;
  optimization_score: number;
  estimated_speedup: string;
  estimated_savings: string;
  suggestions: SuggestionItem[];
  optimized_workflow_graph?: any;
}

interface WorkflowOptimizerModalProps {
  isOpen: boolean;
  onClose: () => void;
  optimizerData: OptimizerData | null;
  onApplyOptimization: () => void;
}

export const WorkflowOptimizerModal: React.FC<WorkflowOptimizerModalProps> = ({
  isOpen,
  onClose,
  optimizerData,
  onApplyOptimization,
}) => {
  if (!isOpen || !optimizerData) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">AI Workflow Optimizer</h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Automated Speedup & Cost Reduction Analysis</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[75vh]">
          {/* Score Cards */}
          <div className="grid grid-cols-4 gap-3">
            <div className="p-3 bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/50 rounded-xl text-center">
              <div className="text-[10px] uppercase font-semibold text-indigo-600 dark:text-indigo-400">Perf Score</div>
              <div className="text-xl font-extrabold text-indigo-900 dark:text-indigo-200">{optimizerData.performance_score}/100</div>
            </div>

            <div className="p-3 bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/50 rounded-xl text-center">
              <div className="text-[10px] uppercase font-semibold text-emerald-600 dark:text-emerald-400">Opti Score</div>
              <div className="text-xl font-extrabold text-emerald-900 dark:text-emerald-200">{optimizerData.optimization_score}/100</div>
            </div>

            <div className="p-3 bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800/50 rounded-xl text-center">
              <div className="text-[10px] uppercase font-semibold text-blue-600 dark:text-blue-400 flex items-center justify-center space-x-1">
                <TrendingUp className="w-3 h-3" />
                <span>Speedup</span>
              </div>
              <div className="text-sm font-bold text-blue-900 dark:text-blue-200 mt-1">{optimizerData.estimated_speedup}</div>
            </div>

            <div className="p-3 bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 rounded-xl text-center">
              <div className="text-[10px] uppercase font-semibold text-amber-600 dark:text-amber-400 flex items-center justify-center space-x-1">
                <DollarSign className="w-3 h-3" />
                <span>Savings</span>
              </div>
              <div className="text-xs font-bold text-amber-900 dark:text-amber-200 mt-1">{optimizerData.estimated_savings}</div>
            </div>
          </div>

          {/* Suggestion List */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Detected Optimization Opportunities
            </h4>
            <div className="space-y-2">
              {optimizerData.suggestions.map((sug) => (
                <div
                  key={sug.id}
                  className="p-3 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 rounded-xl text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-900 dark:text-white">{sug.title}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        sug.impact === 'High'
                          ? 'bg-rose-100 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300'
                          : 'bg-amber-100 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300'
                      }`}
                    >
                      {sug.impact} Impact
                    </span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-300">{sug.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Action */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-between">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Clicking apply mutates your graph topology & parameters.
          </span>
          <button
            onClick={onApplyOptimization}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md transition flex items-center space-x-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>One-Click Apply Optimization</span>
          </button>
        </div>
      </div>
    </div>
  );
};
