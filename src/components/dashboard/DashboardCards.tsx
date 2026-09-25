import React from 'react';
import { motion } from 'framer-motion';
import { Workflow, CheckCircle2, Clock, RotateCcw, TrendingUp } from 'lucide-react';
import type { AnalyticsOverview } from '../../types/analytics';

export const DashboardCards: React.FC<{ analytics?: Partial<AnalyticsOverview> }> = ({ analytics }) => {
  const hasTotal = analytics?.total_executions !== undefined && analytics?.total_executions !== null;
  const hasSucc = analytics?.successful_executions !== undefined && analytics?.successful_executions !== null;
  const hasRate = analytics?.success_rate_pct !== undefined && analytics?.success_rate_pct !== null;
  const hasAvg = analytics?.avg_duration_ms !== undefined && analytics?.avg_duration_ms !== null;
  const hasRetries = analytics?.total_retries !== undefined && analytics?.total_retries !== null;

  const cards = [
    {
      title: 'Total Executions',
      value: hasTotal && analytics?.total_executions !== undefined ? analytics.total_executions.toLocaleString() : '—',
      badge: 'Real-time Telemetry',
      icon: Workflow,
      iconBg: 'bg-[#FF6D00]/15 border border-[#FF6D00]/30 text-[#FF6D00]',
      glowColor: 'group-hover:shadow-[0_0_25px_rgba(255,109,0,0.20)]',
      accentBorder: 'hover:border-[#FF6D00]/40',
    },
    {
      title: 'Successful Runs',
      value: hasSucc && analytics?.successful_executions !== undefined ? analytics.successful_executions.toLocaleString() : '—',
      badge: hasRate && analytics?.success_rate_pct !== undefined ? `${analytics.success_rate_pct}% Success Rate` : 'Active Protection',
      icon: CheckCircle2,
      iconBg: 'bg-[#22C55E]/15 border border-[#22C55E]/30 text-[#22C55E]',
      glowColor: 'group-hover:shadow-[0_0_25px_rgba(34,197,94,0.20)]',
      accentBorder: 'hover:border-[#22C55E]/40',
    },
    {
      title: 'Avg Latency',
      value: hasAvg && analytics?.avg_duration_ms !== undefined ? `${analytics.avg_duration_ms}ms` : '—',
      badge: 'Average Execution Duration',
      icon: Clock,
      iconBg: 'bg-[#F59E0B]/15 border border-[#F59E0B]/30 text-[#F59E0B]',
      glowColor: 'group-hover:shadow-[0_0_25px_rgba(245,158,11,0.20)]',
      accentBorder: 'hover:border-[#F59E0B]/40',
    },

    {
      title: 'Retries & Saga',
      value: hasRetries && analytics?.total_retries !== undefined ? analytics.total_retries.toLocaleString() : '—',
      badge: 'Fault Recovery Active',
      icon: RotateCcw,
      iconBg: 'bg-[#A855F7]/15 border border-[#A855F7]/30 text-[#A855F7]',
      glowColor: 'group-hover:shadow-[0_0_25px_rgba(168,85,247,0.20)]',
      accentBorder: 'hover:border-[#A855F7]/40',
    },
  ];


  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: idx * 0.06, ease: 'easeOut' }}
            className={`group relative p-5 rounded-2xl bg-[#1B1728]/85 border border-[rgba(255,255,255,0.12)] shadow-xl backdrop-blur-2xl transition-all duration-300 ${card.accentBorder} ${card.glowColor}`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] font-bold text-[rgba(255,255,255,0.50)] uppercase tracking-wider">
                {card.title}
              </span>
              <div className={`p-2 rounded-xl flex items-center justify-center ${card.iconBg}`}>
                <Icon className="h-4 w-4" />
              </div>
            </div>

            <div className="space-y-1.5">
              <p className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                {card.value}
              </p>
              <div className="flex items-center gap-1.5">
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[rgba(255,255,255,0.65)]">
                  <TrendingUp className="h-3 w-3 text-[#FF6D00]" />
                  {card.badge}
                </span>
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};

