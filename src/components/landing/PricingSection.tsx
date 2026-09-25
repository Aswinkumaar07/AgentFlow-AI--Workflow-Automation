import { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLandingTheme } from '../../context/LandingThemeContext';


const plans = [
  {
    name: 'Free',
    price: { monthly: 0, annual: 0 },
    description: 'Perfect for exploring AgentFlow and personal projects.',
    features: ['5 workflows', '100 executions/month', '2 AI agents', 'Basic analytics', 'Community support'],
    cta: 'Get Started Free',
    popular: false,
  },
  {
    name: 'Pro',
    price: { monthly: 29, annual: 19 },
    description: 'For professionals and small teams shipping automations at scale.',
    features: ['Unlimited workflows', '10,000 executions/month', 'All AI agents', 'Advanced analytics', 'API key management', 'Priority support', 'Webhook triggers'],
    cta: 'Start Pro Trial',
    popular: true,
  },
  {
    name: 'Enterprise',
    price: { monthly: 99, annual: 79 },
    description: 'For organizations requiring compliance, scale, and SLAs.',
    features: ['Unlimited everything', 'Custom AI agents', 'SSO & RBAC', 'Audit logs', 'Custom integrations', 'Dedicated support', 'SLA guarantee'],
    cta: 'Contact Sales',
    popular: false,
  },
];

export function PricingSection() {
  const [annual, setAnnual] = useState(false);
  const { theme } = useLandingTheme();
  const isDark = theme === 'dark';

  const sectionBg     = isDark ? '#09090B'  : '#FFFFFF';
  const textPrimary   = isDark ? '#F8FAFC'  : '#0F172A';
  const textMuted     = isDark ? '#64748B'  : '#64748B';
  const cardBg        = isDark ? '#18181B'  : '#F8FAFC';
  const cardBorder    = isDark ? '#27272A'  : '#E4E4E7';
  const toggleBg      = isDark ? '#18181B'  : '#F1F5F9';
  const toggleBorder  = isDark ? '#27272A'  : '#E2E8F0';
  const inactiveText  = isDark ? '#64748B'  : '#94A3B8';
  const featureText   = isDark ? '#94A3B8'  : '#475569';
  const planNameColor = isDark ? '#F8FAFC'  : '#0F172A';
  const priceColor    = isDark ? '#F8FAFC'  : '#0F172A';

  return (
    <section id="pricing" className="py-24" style={{ backgroundColor: sectionBg }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <motion.p initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="text-sm font-medium uppercase tracking-widest mb-4" style={{ color: '#6366F1' }}>
            Pricing
          </motion.p>
          <motion.h2 initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
            className="text-3xl sm:text-4xl font-bold mb-4" style={{ color: textPrimary }}>
            Simple, transparent pricing
          </motion.h2>

          {/* Monthly / Annual toggle */}
          <div className="inline-flex items-center gap-1 rounded-xl p-1 mt-4"
            style={{ backgroundColor: toggleBg, border: `1px solid ${toggleBorder}` }}>
            <button
              onClick={() => setAnnual(false)}
              className="px-4 py-1.5 rounded-lg text-sm transition-all font-medium"
              style={!annual
                ? { backgroundColor: '#6366F1', color: '#fff', boxShadow: '0 2px 8px rgba(99,102,241,0.4)' }
                : { color: inactiveText, backgroundColor: 'transparent' }}>
              Monthly
            </button>
            <button
              onClick={() => setAnnual(true)}
              className="flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm transition-all font-medium"
              style={annual
                ? { backgroundColor: '#6366F1', color: '#fff', boxShadow: '0 2px 8px rgba(99,102,241,0.4)' }
                : { color: inactiveText, backgroundColor: 'transparent' }}>
              Annual <span className="text-[10px] bg-[#22C55E]/20 text-[#22C55E] px-1.5 py-0.5 rounded-full">-35%</span>
            </button>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {plans.map((plan, i) => (
            <motion.div key={plan.name}
              initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
              className="relative rounded-2xl border p-6 flex flex-col transition-all duration-300"
              style={plan.popular
                ? { backgroundColor: isDark ? 'rgba(99,102,241,0.06)' : 'rgba(99,102,241,0.04)', borderColor: 'rgba(99,102,241,0.4)', boxShadow: '0 8px 32px rgba(99,102,241,0.15)' }
                : { backgroundColor: cardBg, borderColor: cardBorder, boxShadow: isDark ? 'none' : '0 1px 4px rgba(0,0,0,0.06)' }}>

              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="flex items-center gap-1 px-3 py-1 text-xs font-semibold rounded-full text-white"
                    style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)' }}>
                    <Zap className="w-3 h-3" /> Most Popular
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-lg font-bold mb-1" style={{ color: planNameColor }}>{plan.name}</h3>
                <p className="text-xs mb-4" style={{ color: textMuted }}>{plan.description}</p>
                <div className="flex items-end gap-1">
                  <span className="text-4xl font-bold" style={{ color: priceColor }}>
                    ${annual ? plan.price.annual : plan.price.monthly}
                  </span>
                  {plan.price.monthly > 0 && <span className="text-sm mb-1" style={{ color: textMuted }}>/mo</span>}
                </div>
              </div>

              <ul className="space-y-3 flex-1 mb-6">
                {plan.features.map(f => (
                  <li key={f} className="flex items-center gap-2.5 text-sm" style={{ color: featureText }}>
                    <Check className="w-4 h-4 shrink-0 text-[#22C55E]" /> {f}
                  </li>
                ))}
              </ul>

              <Link to="/register">
                <button
                  className="w-full py-2.5 rounded-xl text-sm font-semibold transition-all"
                  style={plan.popular
                    ? { background: 'linear-gradient(135deg, #6366F1, #8B5CF6)', color: '#fff', boxShadow: '0 4px 14px rgba(99,102,241,0.35)' }
                    : { backgroundColor: isDark ? '#27272A' : '#F1F5F9', color: isDark ? '#F8FAFC' : '#0F172A', border: `1px solid ${cardBorder}` }}
                  onMouseEnter={e => {
                    if (!plan.popular) {
                      (e.currentTarget as HTMLButtonElement).style.backgroundColor = isDark ? '#3F3F46' : '#E2E8F0';
                    } else {
                      (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-1px)';
                    }
                  }}
                  onMouseLeave={e => {
                    if (!plan.popular) {
                      (e.currentTarget as HTMLButtonElement).style.backgroundColor = isDark ? '#27272A' : '#F1F5F9';
                    } else {
                      (e.currentTarget as HTMLButtonElement).style.transform = 'none';
                    }
                  }}>
                  {plan.cta}
                </button>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
