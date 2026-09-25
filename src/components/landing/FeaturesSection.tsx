import { motion } from 'framer-motion';
import { Wand2, Zap, Shield, BarChart3, GitBranch, Globe, ArrowRight } from 'lucide-react';
import { useLandingTheme } from '../../context/LandingThemeContext';
import { useRef } from 'react';

/* ─── Bento Feature Data ─────────────────────────────────── */
const bentoItems = [
  {
    id: 'a',
    icon: Wand2,
    title: 'Natural Language Builder',
    description: 'Describe your workflow in plain English. Our AI understands intent and builds the exact automation you need — no code, no diagrams.',
    color: '#6366F1',
    size: 'large',   // spans 2 cols
    preview: (
      <div className="mt-4 space-y-2 relative z-10">
        {[
          '"When a GitHub PR is opened, create a Jira ticket"',
          '"Send a Slack alert if Stripe payment fails"',
          '"Summarize emails and add to Notion daily"',
        ].map((text, i) => (
          <div key={i} className="flex items-start gap-2 opacity-90">
            <span className="text-[#6366F1] text-xs mt-0.5">›</span>
            <p className="text-xs italic" style={{ color: 'inherit' }}>{text}</p>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 'b',
    icon: Zap,
    title: 'Multi-Agent Execution',
    description: 'Planner, Executor, Validator agents run in parallel for reliable, self-correcting automations.',
    color: '#8B5CF6',
    size: 'small',
    preview: (
      <div className="mt-3 flex flex-col gap-1.5 relative z-10">
        {[{ label: 'Planner Agent', pct: 100 }, { label: 'Executor', pct: 82 }, { label: 'Validator', pct: 60 }].map(a => (
          <div key={a.label}>
            <div className="flex justify-between text-[10px] mb-0.5" style={{ color: 'inherit' }}>
              <span>{a.label}</span><span>{a.pct}%</span>
            </div>
            <div className="h-1 rounded-full overflow-hidden" style={{ backgroundColor: 'rgba(139,92,246,0.15)' }}>
              <motion.div className="h-full rounded-full" style={{ backgroundColor: '#8B5CF6' }}
                initial={{ width: 0 }} whileInView={{ width: `${a.pct}%` }}
                transition={{ duration: 1, delay: 0.3 }} viewport={{ once: true }} />
            </div>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 'c',
    icon: Shield,
    title: 'RAG-Powered Intelligence',
    description: 'Retrieval-Augmented Generation keeps AI current with your API docs and workflow history.',
    color: '#22C55E',
    size: 'small',
    preview: (
      <div className="mt-3 flex flex-wrap gap-1.5 relative z-10">
        {['API Docs', 'Workflow History', 'Schema Cache', 'Error Patterns', 'Best Practices'].map(tag => (
          <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full font-medium"
            style={{ backgroundColor: 'rgba(34,197,94,0.12)', color: '#22C55E', border: '1px solid rgba(34,197,94,0.25)' }}>
            {tag}
          </span>
        ))}
      </div>
    ),
  },
  {
    id: 'd',
    icon: BarChart3,
    title: 'Advanced Analytics',
    description: 'Monitor execution metrics, success rates, API latency, and cost in one beautiful dashboard.',
    color: '#06B6D4',
    size: 'small',
    preview: (
      <div className="mt-3 grid grid-cols-3 gap-2 relative z-10">
        {[{ v: '97.4%', l: 'Success' }, { v: '1.2s', l: 'Avg time' }, { v: '2.8k', l: 'Tokens' }].map(m => (
          <div key={m.l} className="text-center rounded-xl p-2" style={{ backgroundColor: 'rgba(6,182,212,0.08)' }}>
            <p className="text-sm font-bold" style={{ color: '#06B6D4' }}>{m.v}</p>
            <p className="text-[9px] mt-0.5" style={{ color: 'inherit', opacity: 0.7 }}>{m.l}</p>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 'e',
    icon: GitBranch,
    title: 'Visual Workflow Graph',
    description: 'Live interactive DAG — every node, edge and dependency visualized in real time with drag-and-drop editing.',
    color: '#F59E0B',
    size: 'medium',
    preview: (
      <div className="mt-3 flex items-center gap-2 relative z-10">
        {['Trigger', 'AI Extract', 'Condition', 'Action'].map((n, i) => (
          <div key={n} className="flex items-center gap-2">
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 rounded-xl flex items-center justify-center text-[10px] font-bold"
                style={{ backgroundColor: 'rgba(245,158,11,0.12)', color: '#F59E0B', border: '1px solid rgba(245,158,11,0.25)' }}>
                {i + 1}
              </div>
              <p className="text-[8px] mt-1 text-center" style={{ color: 'inherit', opacity: 0.7, maxWidth: 40 }}>{n}</p>
            </div>
            {i < 3 && <div className="w-4 h-px" style={{ backgroundColor: '#F59E0B', opacity: 0.4 }} />}
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 'f',
    icon: Globe,
    title: '200+ Integrations',
    description: 'GitHub, Slack, Stripe, Notion, Jira, HubSpot and hundreds more.',
    color: '#6366F1',
    size: 'medium',
    preview: (
      <div className="mt-3 grid grid-cols-4 gap-2 relative z-10">
        {['🐙', '💬', '💳', '📝', '🎫', '📊', '🔗', '⚡'].map((emoji, i) => (
          <div key={i} className="w-8 h-8 rounded-xl flex items-center justify-center text-base"
            style={{ backgroundColor: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)' }}>
            {emoji}
          </div>
        ))}
      </div>
    ),
  },
];

/* ─── Spotlight Card Helper ──────────────────────────────────── */
function BentoCard({ item, colSpan, cardStyle, textPrimary, textBody }: {
  item: typeof bentoItems[0];
  colSpan: string;
  cardStyle: (color: string) => React.CSSProperties;
  textPrimary: string;
  textBody: string;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const Icon = item.icon;

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    cardRef.current.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
    cardRef.current.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
  };

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4 }}
      className={`${colSpan} spotlight-card rounded-3xl p-6 group cursor-default relative overflow-hidden transition-all duration-300`}
      style={cardStyle(item.color)}
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      whileHover={{ y: -4 } as any}
    >
      <div className="absolute top-0 right-0 w-48 h-48 rounded-full blur-3xl opacity-15 group-hover:opacity-30 transition-opacity"
        style={{ background: `radial-gradient(circle, ${item.color}, transparent)` }} />
      <div className="w-10 h-10 rounded-2xl flex items-center justify-center mb-4 relative z-10"
        style={{ backgroundColor: `${item.color}18`, border: `1px solid ${item.color}30` }}>
        <Icon className="w-5 h-5" style={{ color: item.color }} />
      </div>
      <h3 className="text-xl font-bold mb-2 relative z-10" style={{ color: textPrimary }}>{item.title}</h3>
      <p className="text-sm leading-relaxed relative z-10" style={{ color: textBody }}>{item.description}</p>
      {item.preview}
      {item.size === 'large' && (
        <div className="flex items-center gap-1 mt-4 text-xs font-medium relative z-10" style={{ color: item.color }}>
          Learn more <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 translate-x-0 group-hover:translate-x-1 transition-all" />
        </div>
      )}
    </motion.div>
  );
}

export function FeaturesSection() {
  const { theme } = useLandingTheme();
  const isDark = theme === 'dark';

  const sectionBg   = isDark ? '#09090B'  : '#F1F5F9';
  const cardBg      = isDark ? '#111827'  : '#FFFFFF';
  const cardBorder  = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
  const textPrimary = isDark ? '#F8FAFC'  : '#0F172A';
  const textMuted   = isDark ? '#94A3B8'  : '#64748B';
  const textBody    = isDark ? '#D4D4D8'  : '#475569';

  const row1 = bentoItems.filter(b => ['a', 'b', 'c'].includes(b.id));
  const row2 = bentoItems.filter(b => ['d', 'e', 'f'].includes(b.id));

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const cardStyle = (_color: string) => ({
    backgroundColor: cardBg,
    border: `1px solid ${cardBorder}`,
    boxShadow: isDark
      ? `0 1px 0 rgba(255,255,255,0.04) inset, 0 4px 24px rgba(0,0,0,0.4)`
      : `0 1px 3px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.04)`,
    color: textBody,
  });

  return (
    <section id="features" className="py-24 relative" style={{ backgroundColor: sectionBg }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-14">
          <motion.p initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="text-sm font-semibold uppercase tracking-widest mb-4" style={{ color: '#6366F1' }}>
            Features
          </motion.p>
          <motion.h2 initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
            className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 leading-tight" style={{ color: textPrimary, fontFamily: 'var(--font-display)' }}>
            Everything to automate at scale
          </motion.h2>
          <motion.p initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }}
            className="max-w-2xl mx-auto text-lg" style={{ color: textMuted }}>
            AgentFlow combines Large Language Models with battle-tested workflow orchestration to deliver automations that work reliably.
          </motion.p>
        </div>

        {/* ── Bento Grid ────────────────────────────────────── */}
        <div className="space-y-4">
          {/* Row 1 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <BentoCard item={row1[0]} colSpan="md:col-span-2" cardStyle={cardStyle} textPrimary={textPrimary} textBody={textBody} />
            <BentoCard item={row1[1]} colSpan="md:col-span-1" cardStyle={cardStyle} textPrimary={textPrimary} textBody={textBody} />
            <BentoCard item={row1[2]} colSpan="md:col-span-1" cardStyle={cardStyle} textPrimary={textPrimary} textBody={textBody} />
          </div>

          {/* Row 2 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <BentoCard item={row2[0]} colSpan="md:col-span-1" cardStyle={cardStyle} textPrimary={textPrimary} textBody={textBody} />
            <BentoCard item={row2[1]} colSpan="md:col-span-2" cardStyle={cardStyle} textPrimary={textPrimary} textBody={textBody} />
            <BentoCard item={row2[2]} colSpan="md:col-span-1" cardStyle={cardStyle} textPrimary={textPrimary} textBody={textBody} />
          </div>
        </div>
      </div>
    </section>
  );
}
