import React, { useState } from 'react';
import { Bot, Send, RotateCcw, CheckCircle2, Cpu, Terminal } from 'lucide-react';
import { apiClient } from '../../api/client';

export interface ActionStepItem {
  step_id: string;
  action_type: string;
  provider: string;
  operation: string;
  reasoning: string;
  confidence: number;
  requires_human_approval: boolean;
  approval_status: string;
  status: string;
  input_payload: any;
  output_response: any;
}

export interface AutonomousResult {
  execution_id: string;
  goal: string;
  overall_confidence: number;
  human_approval_required: boolean;
  approval_prompt?: string;
  outcome_summary: string;
  action_trace: ActionStepItem[];
  audit_logs: string[];
  can_rollback: boolean;
}

export const AutonomousAgentConsole: React.FC = () => {
  const [goal, setGoal] = useState<string>('Handle customer refunds automatically');
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [result, setResult] = useState<AutonomousResult | null>(null);

  const handleExecuteGoal = async () => {
    if (!goal.trim()) return;
    setIsExecuting(true);

    try {
      const resp = await apiClient.post('/autonomous/execute-goal', {
        goal: goal,
      });
      setResult(resp.data);
    } catch {
      alert('Autonomous execution failed.');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleRollback = async () => {
    if (!result) return;
    try {
      const resp = await apiClient.post('/autonomous/rollback', result);
      setResult(resp.data);
    } catch {
      alert('Rollback failed.');
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-6 animate-fade-in">
      {/* Flagship Header Banner */}
      <div className="p-6 bg-gradient-to-r from-indigo-900 via-slate-900 to-purple-950 border border-indigo-500/30 rounded-2xl text-white shadow-2xl relative overflow-hidden">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/50">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-mono tracking-widest text-indigo-400 font-bold">
              Flagship AI Capability • AgentFlow v2.0
            </div>
            <h2 className="text-xl font-black">Autonomous Workflow Agent</h2>
          </div>
        </div>
        <p className="mt-2 text-xs text-indigo-200 leading-relaxed max-w-2xl">
          Describe high-level outcomes instead of building static DAGs. AI reads emails, checks CRM & Stripe, approves/rejects, logs audit trails, and asks for human approval when thresholds require it.
        </p>
      </div>

      {/* Goal Prompt Bar */}
      <div className="flex items-center space-x-3 bg-white dark:bg-slate-900 p-2.5 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm">
        <div className="relative flex-1">
          <Cpu className="w-5 h-5 absolute left-3.5 top-3.5 text-indigo-500" />
          <input
            type="text"
            placeholder="Describe an outcome goal... e.g. Handle customer refunds automatically"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleExecuteGoal()}
            className="w-full pl-11 pr-4 py-3 bg-transparent text-sm text-slate-900 dark:text-white focus:outline-none font-medium"
          />
        </div>
        <button
          onClick={handleExecuteGoal}
          disabled={isExecuting || !goal.trim()}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-xl text-xs font-bold shadow-md transition flex items-center space-x-2 shrink-0"
        >
          <Send className="w-4 h-4" />
          <span>{isExecuting ? 'Reasoning & Executing...' : 'Execute Outcome Goal'}</span>
        </button>
      </div>

      {/* Results & Live Action Trace */}
      {result && (
        <div className="space-y-6">
          {/* Summary & Metrics */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-1">
              <div className="text-[10px] uppercase font-bold text-slate-400">Overall Confidence</div>
              <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                {int(result.overall_confidence * 100)}%
              </div>
            </div>

            <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-1">
              <div className="text-[10px] uppercase font-bold text-slate-400">Actions Executed</div>
              <div className="text-2xl font-black text-indigo-600 dark:text-indigo-400">
                {result.action_trace.length} Steps
              </div>
            </div>

            <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm space-y-1">
              <div className="text-[10px] uppercase font-bold text-slate-400">Rollback Status</div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-slate-700 dark:text-slate-200">
                  {result.can_rollback ? 'Available' : 'Rolled Back'}
                </span>
                {result.can_rollback && (
                  <button
                    onClick={handleRollback}
                    className="px-3 py-1 bg-rose-100 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300 rounded-lg text-xs font-bold hover:bg-rose-200 transition flex items-center space-x-1"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Rollback</span>
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Outcome Summary */}
          <div className="p-4 bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/50 rounded-2xl flex items-center space-x-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
            <div className="text-xs font-medium text-emerald-900 dark:text-emerald-200">
              {result.outcome_summary}
            </div>
          </div>

          {/* Action Trace Timeline */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 space-y-4 shadow-sm">
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-indigo-600" />
              <span>Dynamic ReAct Action Trace</span>
            </h3>

            <div className="space-y-3">
              {result.action_trace.map((step, idx) => (
                <div
                  key={step.step_id}
                  className="p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 rounded-xl space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 font-bold text-slate-900 dark:text-white">
                      <span className="w-5 h-5 rounded-full bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 flex items-center justify-center text-[10px]">
                        {idx + 1}
                      </span>
                      <span>{step.action_type}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-mono">
                        {step.provider}
                      </span>
                    </div>

                    <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                      Confidence: {int(step.confidence * 100)}%
                    </span>
                  </div>

                  <p className="text-slate-600 dark:text-slate-300">{step.reasoning}</p>

                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
                    <span>Op: {step.operation}</span>
                    <span
                      className={`font-semibold ${
                        step.status === 'executed'
                          ? 'text-emerald-600'
                          : step.status === 'rolled_back'
                          ? 'text-rose-500'
                          : 'text-amber-500'
                      }`}
                    >
                      Status: {step.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Audit Logs Terminal */}
          <div className="bg-slate-950 rounded-2xl p-5 border border-slate-800 space-y-2">
            <div className="text-[11px] font-semibold text-slate-400 uppercase flex items-center space-x-1.5 font-mono">
              <Terminal className="w-3.5 h-3.5 text-indigo-400" />
              <span>Immutable Execution Audit Log</span>
            </div>
            <div className="space-y-1 font-mono text-xs text-slate-300 max-h-48 overflow-y-auto">
              {result.audit_logs.map((log, i) => (
                <div key={i} className="text-[11px] leading-relaxed">
                  {log}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function int(val: number): number {
  return Math.round(val);
}
