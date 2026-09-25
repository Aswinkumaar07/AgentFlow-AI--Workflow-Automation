import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import { useLandingTheme } from '../../context/LandingThemeContext';

export function CTASection() {
  const { theme } = useLandingTheme();
  const isDark = theme === 'dark';

  const sectionBg  = isDark ? '#030712'  : '#F8FAFC';
  const textPrimary= isDark ? '#F9FAFB'  : '#0F172A';
  const textMuted  = isDark ? '#9CA3AF'  : '#64748B';
  const gridLine   = isDark ? '#1F2937'  : '#CBD5E1';
  const cardBorder = isDark ? '#374151'  : '#CBD5E1';

  return (
    <section className="py-24 relative overflow-hidden" style={{ backgroundColor: sectionBg }}>
      {/* Background gradients */}
      <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse 70% 60% at 50% 50%, rgba(66,133,244,0.15) 0%, rgba(147,51,234,0.08) 50%, transparent 100%)' }} />
      <div className="absolute inset-0 opacity-15" style={{
        backgroundImage: `linear-gradient(to right, ${gridLine} 1px, transparent 1px), linear-gradient(to bottom, ${gridLine} 1px, transparent 1px)`,
        backgroundSize: '48px 48px',
      }} />

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>

          <div className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm mb-6"
            style={{ backgroundColor: 'rgba(66,133,244,0.12)', border: '1px solid rgba(66,133,244,0.3)', color: '#60A5FA' }}>
            <Sparkles className="w-3.5 h-3.5 text-[#EC4899]" /> Start building for free today
          </div>

          <h2 className="text-4xl sm:text-5xl font-bold mb-5 leading-tight" style={{ color: textPrimary, fontFamily: 'var(--font-display)' }}>
            Ready to automate your<br />
            <span className="gemini-gradient-text">
              API workflows?
            </span>
          </h2>

          <p className="text-lg mb-8 max-w-xl mx-auto" style={{ color: textMuted }}>
            Join thousands of developers who use AgentFlow AI to build intelligent automations in minutes, not days.
          </p>

          <div className="flex flex-wrap gap-4 justify-center">
            <Link to="/register">
              <button
                className="flex items-center gap-2 px-7 py-3.5 rounded-xl font-semibold text-white transition-all gemini-gradient-bg shadow-lg"
                style={{ boxShadow: '0 8px 28px rgba(66,133,244,0.4)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-2px)'; (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 12px 32px rgba(147,51,234,0.55)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'none'; (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 8px 28px rgba(66,133,244,0.4)'; }}>
                <Sparkles className="w-4 h-4 text-white" /> Get Started Free <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
            <Link to="/login">
              <button
                className="flex items-center gap-2 px-7 py-3.5 rounded-xl font-semibold transition-all"
                style={{ color: textPrimary, border: `2px solid ${cardBorder}`, backgroundColor: 'transparent' }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = '#4285F4'; (e.currentTarget as HTMLButtonElement).style.color = '#4285F4'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = cardBorder; (e.currentTarget as HTMLButtonElement).style.color = textPrimary; }}>
                Sign in to Dashboard
              </button>
            </Link>
          </div>

          <p className="text-xs mt-6" style={{ color: textMuted }}>
            No credit card required · Free forever plan · Setup in 2 minutes
          </p>
        </motion.div>
      </div>
    </section>
  );
}
