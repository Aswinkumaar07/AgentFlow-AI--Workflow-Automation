import { motion } from 'framer-motion';
import { Star } from 'lucide-react';
import { useLandingTheme } from '../../context/LandingThemeContext';

const testimonials = [
  { name: 'Sarah Chen',   role: 'CTO at TechForward',       avatar: 'SC', stars: 5, content: 'AgentFlow completely changed how we handle API integrations. What used to take days of engineering work now takes minutes. The AI actually understands what we want.' },
  { name: 'Marcus Webb',  role: 'Lead Developer at DevScale', avatar: 'MW', stars: 5, content: 'I was skeptical at first, but the quality of the generated workflows is impressive. It correctly handles edge cases and even validates the workflow before execution.' },
  { name: 'Priya Nair',   role: 'Product Manager at Flowbase', avatar: 'PN', stars: 5, content: 'Our non-technical team members can now create automations without involving the dev team. AgentFlow democratized workflow creation for our entire organization.' },
];

export function Testimonials() {
  const { theme } = useLandingTheme();
  const isDark = theme === 'dark';

  const sectionBg  = isDark ? 'rgba(17,24,39,0.2)' : '#F8FAFC';
  const cardBg     = isDark ? '#18181B'             : '#FFFFFF';
  const cardBorder = isDark ? '#27272A'             : '#E4E4E7';
  const cardHover  = isDark ? 'rgba(99,102,241,0.2)': 'rgba(99,102,241,0.15)';
  const textPrimary= isDark ? '#F8FAFC'             : '#0F172A';
  const textMuted  = isDark ? '#94A3B8'             : '#64748B';
  const quoteColor = isDark ? '#94A3B8'             : '#475569';

  return (
    <section className="py-24" style={{ backgroundColor: sectionBg }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <motion.p initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="text-sm font-medium uppercase tracking-widest mb-4" style={{ color: '#6366F1' }}>
            Testimonials
          </motion.p>
          <motion.h2 initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
            className="text-3xl sm:text-4xl font-bold" style={{ color: textPrimary }}>
            Trusted by teams who ship fast
          </motion.h2>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((t, i) => (
            <motion.div key={t.name}
              initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
              className="rounded-2xl border p-6 transition-all duration-300"
              style={{ backgroundColor: cardBg, borderColor: cardBorder, boxShadow: isDark ? 'none' : '0 1px 4px rgba(0,0,0,0.06)' }}
              onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = cardHover; (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-2px)'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = cardBorder; (e.currentTarget as HTMLDivElement).style.transform = 'none'; }}>
              <div className="flex gap-1 mb-4">
                {Array.from({ length: t.stars }).map((_, j) => (
                  <Star key={j} className="w-4 h-4 fill-[#F59E0B] text-[#F59E0B]" />
                ))}
              </div>
              <p className="text-sm leading-relaxed mb-6 italic" style={{ color: quoteColor }}>"{t.content}"</p>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center text-white text-xs font-bold shrink-0">
                  {t.avatar}
                </div>
                <div>
                  <p className="text-sm font-semibold" style={{ color: textPrimary }}>{t.name}</p>
                  <p className="text-xs" style={{ color: textMuted }}>{t.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
