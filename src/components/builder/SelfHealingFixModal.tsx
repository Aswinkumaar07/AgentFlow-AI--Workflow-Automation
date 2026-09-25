import React from 'react';
import { Wrench, X, ShieldAlert, CheckCircle2, Sparkles } from 'lucide-react';

export interface DiagnosticData {
  problem: string;
  cause: string;
  recommendation: string;
  confidence: number;
  proposed_fix_patch: any;
  repaired_workflow_graph?: any;
}

interface SelfHealingFixModalProps {
  isOpen: boolean;
  onClose: () => void;
  diagnostic: DiagnosticData | null;
  onApplyFix: () => void;
}

export const SelfHealingFixModal: React.FC<SelfHealingFixModalProps> = ({
  isOpen,
  onClose,
  diagnostic,
  onApplyFix,
}) => {
  if (!isOpen || !diagnostic) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-rose-600 flex items-center justify-center text-white shadow-sm">
              <Wrench className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Self-Healing Auto-Repair Engine</h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Failure Diagnosis & Automated Structural Fix</p>
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
        <div className="p-6 space-y-4 overflow-y-auto max-h-[70vh]">
          {/* Problem Card */}
          <div className="p-4 bg-rose-50/60 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/50 rounded-xl space-y-1">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-rose-900 dark:text-rose-200">
              <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{diagnostic.problem}</span>
            </div>
            <p className="text-xs text-rose-800 dark:text-rose-300 leading-relaxed">{diagnostic.cause}</p>
          </div>

          {/* Recommendation */}
          <div className="p-4 bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/50 rounded-xl space-y-1">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-indigo-900 dark:text-indigo-200">
              <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0" />
              <span>AI Recommendation & Structural Fix</span>
            </div>
            <p className="text-xs text-indigo-800 dark:text-indigo-300 leading-relaxed">{diagnostic.recommendation}</p>
          </div>

          {/* Patch JSON Code Box */}
          <div className="space-y-1">
            <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">Proposed Patch</div>
            <pre className="p-3 bg-slate-950 text-slate-200 text-xs font-mono rounded-xl overflow-x-auto border border-slate-800">
              {JSON.stringify(diagnostic.proposed_fix_patch, null, 2)}
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-between">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Clicking apply fix updates your workflow canvas automatically.
          </span>
          <button
            onClick={onApplyFix}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md transition flex items-center space-x-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>Apply Fix</span>
          </button>
        </div>
      </div>
    </div>
  );
};
