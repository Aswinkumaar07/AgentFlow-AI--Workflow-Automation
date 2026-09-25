import React from 'react';
import type { ConnectorHealthItem } from '../../types/analytics';
import { CheckCircle2, AlertTriangle, XCircle, Activity } from 'lucide-react';

export const ConnectorHealthGrid: React.FC<{ items?: ConnectorHealthItem[] }> = ({ items = [] }) => {
  if (!Array.isArray(items)) {
    console.error("Expected connector health items array but received:", items);
    return (
      <div className="p-8 text-center text-[rgba(255,255,255,0.4)] border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 rounded-3xl">
        No connector health data available
      </div>
    );
  }

  // Derive dynamic overall health status from existing provider records
  const hasUnavailable = items.some((i) => i.status === 'UNAVAILABLE');
  const hasDegraded = items.some((i) => i.status === 'DEGRADED');

  const overallBadge = hasUnavailable
    ? { text: 'ATTENTION REQUIRED', color: 'text-rose-400 bg-rose-500/10 border-rose-500/20' }
    : hasDegraded
    ? { text: 'SYSTEMS DEGRADED', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' }
    : { text: 'ALL SYSTEMS OPERATIONAL', color: 'text-[#22C55E] bg-[#22C55E]/10 border-[#22C55E]/20' };

  return (
    <div className="rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md p-6 space-y-4 shadow-sm min-w-0 overflow-hidden">
      
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[rgba(255,255,255,0.08)] pb-4 min-w-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="h-10 w-10 rounded-xl bg-[#FF6D00]/10 border border-[#FF6D00]/20 text-[#FF6D00] flex items-center justify-center shrink-0">
            <Activity className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h3 className="font-bold text-sm text-white tracking-tight truncate">Provider Health & Latency</h3>
            <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5 truncate">Real-time latency breakdown across connected API endpoints</p>
          </div>
        </div>

        <span className={`px-2.5 py-1 rounded-lg border text-[10px] font-mono font-bold uppercase tracking-wider shrink-0 self-start sm:self-auto ${overallBadge.color}`}>
          {overallBadge.text}
        </span>
      </div>

      {/* Grid of Provider Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.length === 0 ? (
          <p className="text-xs text-[rgba(255,255,255,0.4)] py-6 col-span-3 text-center">No active connector health records.</p>
        ) : (
          items.map((item) => {
            const isHealthy = item.status === 'HEALTHY';
            const isDegraded = item.status === 'DEGRADED';
            const statusColor = isHealthy
              ? 'text-[#22C55E] bg-[#22C55E]/10 border-[#22C55E]/20'
              : isDegraded
              ? 'text-amber-400 bg-amber-500/10 border-amber-500/20'
              : 'text-rose-400 bg-rose-500/10 border-rose-500/20';

            const StatusIcon = isHealthy ? CheckCircle2 : isDegraded ? AlertTriangle : XCircle;

            return (
              <div
                key={item.provider}
                className="p-4 rounded-2xl border border-[rgba(255,255,255,0.1)] bg-[#1B1728] hover:bg-[#231E3A] hover:border-[rgba(255,255,255,0.18)] transition space-y-3 min-w-0 overflow-hidden shadow-sm"
              >
                <div className="flex items-center justify-between gap-2 min-w-0">
                  <div className="min-w-0 flex-1">
                    <span
                      className="font-extrabold text-xs text-white block truncate"
                      title={item.provider}
                    >
                      {item.provider}
                    </span>
                  </div>

                  <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md border shrink-0 ${statusColor}`}>
                    <StatusIcon className="h-3 w-3 shrink-0" />
                    <span>{item.status}</span>
                  </span>
                </div>

                <div className="flex justify-between items-center text-[11px] text-[rgba(255,255,255,0.6)] font-mono pt-2 border-t border-[rgba(255,255,255,0.08)] gap-2 min-w-0">
                  <span className="truncate">Avg Latency: <strong className="text-[#FF6D00]">{item.avg_latency_ms}ms</strong></span>
                  <span className="shrink-0">Calls: <strong className="text-white">{item.call_count}</strong></span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

