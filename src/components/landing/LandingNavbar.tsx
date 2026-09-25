import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Menu, X, ExternalLink, Moon, Sun } from 'lucide-react';
import { useLandingTheme } from '../../context/LandingThemeContext';

const navLinks = [
  { label: 'Features',    href: '#features'    },
  { label: 'How it Works', href: '#how-it-works' },
  { label: 'Pricing',     href: '#pricing'     },
  { label: 'FAQ',         href: '#faq'         },
];

export function LandingNavbar() {
  const { theme, toggle } = useLandingTheme();
  const [scrolled, setScrolled]   = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const isDark = theme === 'dark';

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handler);
    return () => window.removeEventListener('scroll', handler);
  }, []);

  const navBg = scrolled
    ? isDark
      ? 'rgba(9,9,11,0.92)'
      : 'rgba(255,255,255,0.92)'
    : 'transparent';
  const navBorder = scrolled
    ? isDark ? '1px solid rgba(39,39,42,0.8)' : '1px solid rgba(228,228,231,0.8)'
    : 'none';
  const textColor    = isDark ? '#F8FAFC' : '#0F172A';
  const mutedColor   = isDark ? '#94A3B8' : '#64748B';
  const hoverBg      = isDark ? 'rgba(24,24,27,0.7)' : 'rgba(243,244,246,0.8)';
  const mobileBorder = isDark ? '#27272A' : '#E4E4E7';
  const mobileMenuBg = isDark ? '#09090B' : '#FFFFFF';

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4 }}
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
        backgroundColor: navBg,
        borderBottom: navBorder,
        backdropFilter: scrolled ? 'blur(20px)' : 'none',
        transition: 'background-color 0.3s, border-color 0.3s',
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8.5 h-8.5 rounded-xl bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center shadow-lg shadow-[#6366F1]/30 group-hover:shadow-[#6366F1]/50 transition-shadow">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-base tracking-tight" style={{ color: textColor, fontFamily: 'var(--font-display)' }}>
              AgentFlow <span style={{ color: '#6366F1' }}>AI</span>
            </span>
          </Link>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map(link => (
              <a
                key={link.label}
                href={link.href}
                className="px-3 py-2 text-sm rounded-lg transition-colors font-medium"
                style={{ color: mutedColor }}
                onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.color = textColor; (e.currentTarget as HTMLAnchorElement).style.backgroundColor = hoverBg; }}
                onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.color = mutedColor; (e.currentTarget as HTMLAnchorElement).style.backgroundColor = 'transparent'; }}
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* Desktop right: theme toggle + CTA */}
          <div className="hidden md:flex items-center gap-2">
            {/* Theme toggle */}
            <button
              onClick={toggle}
              className="w-9 h-9 rounded-xl flex items-center justify-center transition-all"
              style={{ backgroundColor: hoverBg, color: mutedColor, border: `1px solid ${mobileBorder}` }}
              aria-label="Toggle theme"
            >
              <AnimatePresence mode="wait" initial={false}>
                {isDark ? (
                  <motion.span key="sun" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.15 }}>
                    <Sun className="w-4 h-4 text-[#F59E0B]" />
                  </motion.span>
                ) : (
                  <motion.span key="moon" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.15 }}>
                    <Moon className="w-4 h-4 text-[#6366F1]" />
                  </motion.span>
                )}
              </AnimatePresence>
            </button>

            {/* Sign in */}
            <Link to="/login">
              <button
                className="px-4 py-2 text-sm rounded-lg font-medium transition-all"
                style={{ color: mutedColor, backgroundColor: 'transparent' }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = hoverBg; (e.currentTarget as HTMLButtonElement).style.color = textColor; }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'transparent'; (e.currentTarget as HTMLButtonElement).style.color = mutedColor; }}
              >
                Sign in
              </button>
            </Link>

            {/* Get Started */}
            <Link to="/builder" onClick={() => localStorage.setItem('agentflow-token', 'demo-token')}>
              <button
                className="flex items-center gap-1.5 px-4 py-2 text-sm rounded-xl font-semibold text-white transition-all shadow-md"
                style={{
                  background: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
                  boxShadow: '0 4px 16px rgba(99,102,241,0.35)',
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 6px 22px rgba(99,102,241,0.55)'; (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-1px)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 4px 16px rgba(99,102,241,0.35)'; (e.currentTarget as HTMLButtonElement).style.transform = 'none'; }}
              >
                Get Started <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </Link>
          </div>

          {/* Mobile: theme + hamburger */}
          <div className="md:hidden flex items-center gap-2">
            <button
              onClick={toggle}
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-all"
              style={{ backgroundColor: hoverBg, color: mutedColor }}
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-4 h-4 text-[#F59E0B]" /> : <Moon className="w-4 h-4 text-[#6366F1]" />}
            </button>
            <button
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-all"
              style={{ color: mutedColor, backgroundColor: hoverBg }}
              onClick={() => setMobileOpen(v => !v)}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        <AnimatePresence>
          {mobileOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8, height: 0 }}
              animate={{ opacity: 1, y: 0, height: 'auto' }}
              exit={{ opacity: 0, y: -8, height: 0 }}
              transition={{ duration: 0.2 }}
              className="md:hidden overflow-hidden"
              style={{ borderTop: `1px solid ${mobileBorder}`, backgroundColor: mobileMenuBg }}
            >
              <div className="py-3 space-y-0.5 px-1">
                {navLinks.map(link => (
                  <a
                    key={link.label}
                    href={link.href}
                    onClick={() => setMobileOpen(false)}
                    className="block px-3 py-2.5 text-sm rounded-xl transition-colors"
                    style={{ color: mutedColor }}
                    onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.color = textColor; (e.currentTarget as HTMLAnchorElement).style.backgroundColor = hoverBg; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.color = mutedColor; (e.currentTarget as HTMLAnchorElement).style.backgroundColor = 'transparent'; }}
                  >
                    {link.label}
                  </a>
                ))}
                <div className="flex gap-2 pt-2 px-2">
                  <Link to="/login" className="flex-1">
                    <button className="w-full py-2.5 text-sm font-medium rounded-xl border transition-all" style={{ color: textColor, borderColor: mobileBorder, backgroundColor: hoverBg }}>
                      Sign in
                    </button>
                  </Link>
                  <Link to="/register" className="flex-1">
                    <button className="w-full py-2.5 text-sm font-semibold rounded-xl text-white" style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)' }}>
                      Get Started
                    </button>
                  </Link>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.nav>
  );
}
