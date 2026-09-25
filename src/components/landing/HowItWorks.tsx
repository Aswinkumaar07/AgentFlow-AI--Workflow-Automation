import { motion } from 'framer-motion';
import { MessageSquare, Cpu, Play } from 'lucide-react';
import { useLandingTheme } from '../../context/LandingThemeContext';

const steps = [
  { number: '01', icon: MessageSquare, title: 'Describe in Plain English',     color: '#6366F1', description: 'Type what you want to automate. No code, no complex diagrams — just natural language like you\'d explain to a teammate.', example: '"When a GitHub PR is opened, create a Jira ticket and notify Slack"' },
  { number: '02', icon: Cpu,           title: 'AI Agents Build Your Workflow', color: '#8B5CF6', description: 'Our multi-agent system — Planner, Executor, Validator — works together to design, verify, and generate your workflow.',   example: '4 specialized agents · RAG-powered · Self-correcting' },
  { number: '03', icon: Play,          title: 'Execute & Monitor',             color: '#22C55E', description: 'Deploy with one click. Watch real-time execution logs, monitor agent decisions, and inspect the generated API calls.',     example: 'Real-time logs · Step-by-step trace · Full observability' },
];

export function HowItWorks() {
  const { theme } = useLandingTheme();
  const isDark = theme === 'dark';

  const sectionBg    = isDark ? 'rgba(17,24,39,0.3)' : '#F8FAFC';
  const borderCol    = isDark ? '#27272A'             : '#E4E4E7';
  const textPrimary  = isDark ? '#F8FAFC'             : '#0F172A';
  const textMuted    = isDark ? '#94A3B8'             : '#64748B';
  const iconBg       = isDark ? '#09090B'             : '#FFFFFF';
  const calloutBg    = isDark ? '#18181B'             : '#FFFFFF';
  const calloutTxt   = isDark ? '#64748B'             : '#94A3B8';

  return (
    <section id="how-it-works" className="py-24" style={{ backgroundColor: sectionBg, borderTop: `1px solid ${borderCol}`, borderBottom: `1px solid ${borderCol}` }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <motion.p initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="text-sm font-medium uppercase tracking-widest mb-4" style={{ color: '#6366F1' }}>
            How it Works
          </motion.p>
          <motion.h2 initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
            className="text-3xl sm:text-4xl font-bold" style={{ color: textPrimary }}>
            From idea to automation in 3 steps
          </motion.h2>
        </div>

        <div className="grid lg:grid-cols-3 gap-8 relative">
          {/* Connecting gradient line */}
          <div className="hidden lg:block absolute top-[60px] left-[calc(16.67%+2rem)] right-[calc(16.67%+2rem)] h-px bg-gradient-to-r from-[#6366F1] via-[#8B5CF6] to-[#22C55E] opacity-50" />

          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <motion.div key={step.title}
                initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.15 }}
                className="relative">
                <div className="flex items-center gap-4 mb-5">
                  <div className="relative flex items-center justify-center w-14 h-14 rounded-2xl border-2 shrink-0"
                    style={{ borderColor: step.color, backgroundColor: iconBg }}>
                    <Icon className="w-6 h-6" style={{ color: step.color }} />
                    <span className="absolute -top-2 -right-2 w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold"
                      style={{ backgroundColor: iconBg, border: `1px solid ${step.color}`, color: step.color }}>
                      {i + 1}
                    </span>
                  </div>
                </div>
                <h3 className="text-lg font-semibold mb-2" style={{ color: textPrimary }}>{step.title}</h3>
                <p className="text-sm leading-relaxed mb-4" style={{ color: textMuted }}>{step.description}</p>
                <div className="rounded-xl p-3" style={{ backgroundColor: calloutBg, border: `1px solid ${borderCol}` }}>
                  <p className="text-xs italic" style={{ color: calloutTxt }}>{step.example}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
