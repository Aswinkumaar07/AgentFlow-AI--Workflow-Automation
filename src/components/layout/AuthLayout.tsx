import { Outlet, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Zap, Sparkles, CheckCircle2, ShieldCheck } from 'lucide-react';

export function AuthLayout() {
  return (
    <div className="min-h-screen flex bg-[var(--bg)] text-[var(--text)] transition-colors relative overflow-hidden">

      {/* Background ambient lighting */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute w-[600px] h-[600px] rounded-full bg-indigo-500/10 blur-[100px] -top-20 -left-20" />
        <div className="absolute w-[500px] h-[500px] rounded-full bg-violet-500/10 blur-[90px] -bottom-20 -right-20" />
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `linear-gradient(to right, #6366F1 1px, transparent 1px), linear-gradient(to bottom, #6366F1 1px, transparent 1px)`,
          backgroundSize: '48px 48px',
        }} />
      </div>

      {/* Left panel — Hero & Live Visual DAG Animation */}
      <div className="hidden lg:flex lg:w-[48%] relative overflow-hidden flex-col justify-between p-12 z-10">
        {/* Deep ambient backdrop */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#6366F1]/30 via-[#8B5CF6]/20 to-transparent backdrop-blur-2xl" />

        {/* Animated DAG node visualizer */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <svg width="460" height="380" viewBox="0 0 460 380" className="opacity-85">
            <defs>
              <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#6366F1" stopOpacity="0.8" />
                <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.8" />
              </linearGradient>
            </defs>

            {/* Glowing connection paths */}
            <motion.path
              d="M 110 190 Q 180 120 250 160"
              stroke="url(#lineGrad)"
              strokeWidth="2.5"
              fill="none"
              strokeDasharray="6 6"
              initial={{ strokeDashoffset: 100 }}
              animate={{ strokeDashoffset: 0 }}
              transition={{ repeat: Infinity, duration: 3, ease: 'linear' }}
            />
            <motion.path
              d="M 250 160 Q 320 140 370 190"
              stroke="url(#lineGrad)"
              strokeWidth="2.5"
              fill="none"
              strokeDasharray="6 6"
              initial={{ strokeDashoffset: 100 }}
              animate={{ strokeDashoffset: 0 }}
              transition={{ repeat: Infinity, duration: 3, ease: 'linear' }}
            />
            <motion.path
              d="M 250 160 Q 280 250 250 300"
              stroke="url(#lineGrad)"
              strokeWidth="2.5"
              fill="none"
              strokeDasharray="6 6"
              initial={{ strokeDashoffset: 100 }}
              animate={{ strokeDashoffset: 0 }}
              transition={{ repeat: Infinity, duration: 3, ease: 'linear' }}
            />

            {/* Interactive Animated Nodes */}
            {[
              { x: 75, y: 175, label: 'GitHub PR', icon: '⚡', color: '#6366F1', delay: 0 },
              { x: 215, y: 145, label: 'Claude AI', icon: '🧠', color: '#8B5CF6', delay: 0.3 },
              { x: 335, y: 175, label: 'Jira Ticket', icon: '🔗', color: '#06B6D4', delay: 0.6 },
              { x: 215, y: 285, label: 'Slack Alert', icon: '💬', color: '#10B981', delay: 0.9 },
            ].map((node) => (
              <motion.g key={node.label} initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, delay: node.delay }}>
                <circle cx={node.x + 35} cy={node.y + 15} r="34" fill="rgba(18, 23, 41, 0.75)" stroke={node.color} strokeWidth="2" className="shadow-2xl" />
                <text x={node.x + 35} y={node.y + 20} textAnchor="middle" fontSize="20">{node.icon}</text>
                <text x={node.x + 35} y={node.y + 62} textAnchor="middle" fontSize="11" fontWeight="700" fill="#FFFFFF" fontFamily="Inter">{node.label}</text>
              </motion.g>
            ))}
          </svg>
        </div>

        {/* Brand Header */}
        <Link to="/" className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center shadow-xl shadow-indigo-500/30">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-extrabold text-white tracking-tight font-display">AgentFlow <span className="text-indigo-400">AI</span></span>
            <span className="text-[10px] text-gray-400 font-medium">Enterprise v2.4</span>
          </div>
        </Link>

        {/* Bottom Tagline & Social Proof */}
        <div className="relative z-10 space-y-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-4">
              <Sparkles className="w-3.5 h-3.5" /> Autonomous AI Multi-Agent Platform
            </div>
            <h2 className="text-3xl font-extrabold text-white leading-tight font-display tracking-tight">
              Build autonomous AI pipelines <br />
              <span className="gradient-text-electric">in seconds with natural language.</span>
            </h2>
          </div>

          {/* Key Feature Bullets */}
          <div className="space-y-2.5">
            {[
              'Describe your workflow in plain English — AI auto-generates the DAG',
              'Connect 100+ APIs: GitHub, Jira, Slack, Stripe, HubSpot & Postgres',
              'Real-time multi-agent execution telemetry & 1-click Python export',
            ].map((feat, i) => (
              <div key={i} className="flex items-center gap-2.5 text-xs text-gray-300 font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{feat}</span>
              </div>
            ))}
          </div>

          {/* Social Proof Quote */}
          <div className="glass-panel rounded-2xl p-4 border border-white/10 shadow-2xl">
            <p className="text-xs text-gray-200 italic leading-relaxed">
              "AgentFlow cut our engineering team's API integration time from 3 weeks to 10 minutes. The visual AI DAG canvas is pure magic."
            </p>
            <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/10">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center text-xs font-extrabold text-white">SC</div>
                <div>
                  <p className="text-xs font-bold text-white">Sarah Chen</p>
                  <p className="text-[10px] text-gray-400">VP of Engineering at TechForward</p>
                </div>
              </div>
              <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                <ShieldCheck className="w-3 h-3" /> SOC2 Certified
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right panel — Form Outlet wrapped in glass container */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12 relative z-10">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
