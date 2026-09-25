import { motion } from 'framer-motion';
import { useLandingTheme } from '../../context/LandingThemeContext';

const technologies = [
  { name: 'React',      color: '#61DAFB' },
  { name: 'FastAPI',    color: '#009688' },
  { name: 'OpenAI',     color: '#74AA9C' },
  { name: 'LangChain',  color: '#4CAF50' },
  { name: 'PostgreSQL', color: '#336791' },
  { name: 'Redis',      color: '#DC382D' },
  { name: 'Docker',     color: '#2496ED' },
  { name: 'TypeScript', color: '#3178C6' },
];

export function TrustBadges() {
  const { theme } = useLandingTheme();
  const isDark = theme === 'dark';
  const sectionBg  = isDark ? 'rgba(17,24,39,0.3)' : '#F1F5F9';
  const borderCol  = isDark ? '#27272A' : '#E2E8F0';
  const badgeBg    = isDark ? '#18181B' : '#FFFFFF';
  const badgeTxt   = isDark ? '#94A3B8' : '#475569';
  const labelColor = isDark ? '#64748B' : '#94A3B8';

  return (
    <section className="py-16" style={{ backgroundColor: sectionBg, borderTop: `1px solid ${borderCol}`, borderBottom: `1px solid ${borderCol}` }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.p initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
          className="text-center text-sm mb-8 uppercase tracking-widest" style={{ color: labelColor }}>
          Built with enterprise-grade technologies
        </motion.p>
        <div className="flex flex-wrap justify-center gap-4">
          {technologies.map((tech, i) => (
            <motion.div key={tech.name}
              initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.07 }}
              className="flex items-center gap-2.5 px-4 py-2 rounded-xl transition-colors"
              style={{ backgroundColor: badgeBg, border: `1px solid ${borderCol}` }}
              onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = isDark ? '#3F3F46' : '#CBD5E1'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = borderCol; }}>
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: tech.color }} />
              <span className="text-sm font-medium" style={{ color: badgeTxt }}>{tech.name}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
