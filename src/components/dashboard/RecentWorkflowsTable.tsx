import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import type { WorkflowHistoryItem } from '../../types/workflow';
import { CheckCircle2, Clock, AlertCircle, ArrowUpRight, Workflow, Plus } from 'lucide-react';

export const RecentWorkflowsTable: React.FC<{ items?: WorkflowHistoryItem[] }> = ({ items = [] }) => {
  if (!Array.isArray(items)) {
    console.error('Expected workflow array but received:', items);
    return (
      <div className="p-8 text-center text-[rgba(255,255,255,0.60)] bg-[#1B1728]/85 border border-[rgba(255,255,255,0.12)] rounded-2xl backdrop-blur-2xl">
        No workflows available
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.2, ease: 'easeOut' }}
      className="rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728]/85 overflow-hidden shadow-2xl backdrop-blur-2xl"
    >
      {/* Table Header */}
      <div className="p-6 border-b border-[rgba(255,255,255,0.10)] flex items-center justify-between">
        <div>
          <h3 className="font-bold text-lg text-white tracking-tight">Recent Workflows</h3>
          <p className="text-xs text-[rgba(255,255,255,0.50)] mt-1 font-medium">
            Live execution telemetry across all connected SaaS providers
          </p>
        </div>
        <Link
          to="/history"
          className="text-xs font-bold text-[#FF6D00] hover:text-[#FF802C] transition flex items-center gap-1 group"
        >
          View All <ArrowUpRight className="h-4 w-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </Link>
      </div>

      {/* Table Content / Empty State */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#13102A]/80 text-[rgba(255,255,255,0.50)] font-bold border-b border-[rgba(255,255,255,0.08)] uppercase tracking-wider">
            <tr>
              <th className="py-3.5 px-6">Workflow Name</th>
              <th className="py-3.5 px-6">Provider</th>
              <th className="py-3.5 px-6">Status</th>
              <th className="py-3.5 px-6">Duration</th>
              <th className="py-3.5 px-6">Executed At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[rgba(255,255,255,0.06)]">
            {items.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-12 text-center">
                  <div className="flex flex-col items-center justify-center max-w-sm mx-auto space-y-3">
                    <div className="h-12 w-12 rounded-2xl bg-[#FF6D00]/10 border border-[#FF6D00]/20 flex items-center justify-center text-[#FF6D00]">
                      <Workflow className="h-6 w-6" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">No recent executions</h4>
                      <p className="text-xs text-[rgba(255,255,255,0.50)] mt-1 font-medium">
                        Run a workflow to see execution activity here.
                      </p>
                    </div>
                    <Link to="/builder">
                      <button className="mt-2 px-4 py-2 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl shadow-[0_4px_16px_rgba(255,109,0,0.30)] hover:brightness-110 transition flex items-center gap-1.5">
                        <Plus className="h-4 w-4" /> Create Workflow
                      </button>
                    </Link>
                  </div>
                </td>
              </tr>
            ) : (
              items.map((item) => {
                const isSuccess = item.status === 'COMPLETED';
                const isWaiting = item.status === 'WAITING_FOR_APPROVAL';

                return (
                  <tr key={item.id} className="hover:bg-[rgba(255,255,255,0.03)] transition-colors">
                    <td className="py-4 px-6 font-semibold text-white">
                      {item.workflow_name}
                    </td>
                    <td className="py-4 px-6 font-mono text-[11px] text-[rgba(255,255,255,0.70)]">
                      <span className="px-2 py-0.5 rounded-md bg-[rgba(255,255,255,0.06)] border border-[rgba(255,255,255,0.10)]">
                        {item.provider}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold ${
                          isSuccess
                            ? 'bg-[#22C55E]/15 text-[#34D399] border border-[#22C55E]/30'
                            : isWaiting
                            ? 'bg-[#06B6D4]/15 text-[#38BDF8] border border-[#06B6D4]/30'
                            : 'bg-[#EF4444]/15 text-[#F87171] border border-[#EF4444]/30'
                        }`}
                      >
                        {isSuccess ? (
                          <CheckCircle2 className="h-3 w-3" />
                        ) : isWaiting ? (
                          <Clock className="h-3 w-3 animate-spin" />
                        ) : (
                          <AlertCircle className="h-3 w-3" />
                        )}
                        {item.status}
                      </span>
                    </td>
                    <td className="py-4 px-6 font-mono text-[11px] text-[rgba(255,255,255,0.65)]">
                      {item.duration_ms}ms
                    </td>
                    <td className="py-4 px-6 text-[rgba(255,255,255,0.55)] font-medium">
                      {new Date(item.executed_at).toLocaleTimeString()}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
};

