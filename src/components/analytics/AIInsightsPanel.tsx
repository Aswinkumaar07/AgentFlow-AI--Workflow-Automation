import React from 'react';
import type { AIInsightItem } from '../../types/analytics';
import { Sparkles, Zap, Lightbulb } from 'lucide-react';

export const AIInsightsPanel: React.FC<{ insights?: AIInsightItem[] }> = ({ insights = [] }) => {
  if (!Array.isArray(insights)) {
    console.error("Expected AI insights array but received:", insights);
    return (
      <div className="p-8 text-center text-[rgba(255,255,255,0.4)] border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 rounded-3xl">
        No AI insights available
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md p-6 space-y-4 shadow-sm min-w-0 overflow-hidden">
      
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-[rgba(255,255,255,0.08)] pb-4 min-w-0">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] text-white flex items-center justify-center font-bold shadow-[0_4px_16px_rgba(255,109,0,0.3)] shrink-0">
          <Sparkles className="h-5 w-5 shrink-0" />
        </div>
        <div className="min-w-0">
          <h3 className="font-bold text-sm text-white tracking-tight truncate">AI Telemetry Optimization Insights</h3>
          <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5 truncate">Automated DAG performance optimization recommendations</p>
        </div>
      </div>

      {/* List of Insight Cards */}
      <div className="space-y-3">
        {insights.length === 0 ? (
          <p className="text-xs text-[rgba(255,255,255,0.4)] py-6 text-center">No optimization suggestions generated.</p>
        ) : (
          insights.map((item) => (
            <div
              key={item.id}
              className="p-4.5 rounded-2xl border border-[rgba(255,255,255,0.1)] bg-[#1B1728] hover:bg-[#231E3A] hover:border-[rgba(255,255,255,0.18)] transition space-y-2 min-w-0 overflow-hidden shadow-sm"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 min-w-0">
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                  <Lightbulb className="h-4 w-4 text-[#FF6D00] shrink-0" />
                  <h4 className="font-bold text-xs text-white truncate" title={item.title}>
                    {item.title}
                  </h4>
                </div>

                {item.potential_time_saved_ms > 0 && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/20 shrink-0 self-start sm:self-auto">
                    <Zap className="h-3 w-3 shrink-0" /> Save ~{item.potential_time_saved_ms}ms
                  </span>
                )}
              </div>

              <p className="text-xs text-[rgba(255,255,255,0.6)] leading-relaxed break-words">
                {item.description}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

