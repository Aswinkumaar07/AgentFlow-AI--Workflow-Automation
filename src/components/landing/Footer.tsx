import { Link } from 'react-router-dom';
import { Zap, X, Code2, Globe2 } from 'lucide-react';
import { useLandingTheme } from '../../context/LandingThemeContext';

const footerLinks = {
  Product:    [{ label: 'Features', href: '#features' }, { label: 'Pricing', href: '#pricing' }, { label: 'Changelog', href: '#' }, { label: 'Roadmap', href: '#' }],
  Developers: [{ label: 'Documentation', href: '#' }, { label: 'API Reference', href: '#' }, { label: 'GitHub', href: '#' }, { label: 'Status', href: '#' }],
  Company:    [{ label: 'About', href: '/about' }, { label: 'Blog', href: '#' }, { label: 'Careers', href: '#' }, { label: 'Contact', href: '#' }],
  Legal:      [{ label: 'Privacy Policy', href: '#' }, { label: 'Terms of Service', href: '#' }, { label: 'Cookie Policy', href: '#' }, { label: 'Security', href: '#' }],
};

export function Footer() {
  const { theme } = useLandingTheme();
  const isDark = theme === 'dark';

  const footerBg     = isDark ? '#09090B'  : '#0F172A';   // always keep footer dark — premium look
  const borderColor  = isDark ? '#27272A'  : '#1E293B';
  const textPrimary  = '#F8FAFC';
  const textMuted    = isDark ? '#64748B'  : '#94A3B8';
  const iconBg       = isDark ? '#18181B'  : '#1E293B';
  const iconBorder   = isDark ? '#27272A'  : '#334155';

  return (
    <footer style={{ backgroundColor: footerBg, borderTop: `1px solid ${borderColor}` }} className="py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link to="/" className="flex items-center gap-2.5 mb-4">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center">
                <Zap className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="font-bold text-sm" style={{ color: textPrimary }}>AgentFlow AI</span>
            </Link>
            <p className="text-xs leading-relaxed mb-4" style={{ color: textMuted }}>
              Intelligent API workflow automation powered by multi-agent AI.
            </p>
            <div className="flex gap-3">
              {[X, Code2, Globe2].map((Icon, i) => (
                <a key={i} href="#"
                  className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
                  style={{ backgroundColor: iconBg, border: `1px solid ${iconBorder}`, color: textMuted }}
                  onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.color = textPrimary; (e.currentTarget as HTMLAnchorElement).style.borderColor = '#4B5563'; }}
                  onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.color = textMuted; (e.currentTarget as HTMLAnchorElement).style.borderColor = iconBorder; }}>
                  <Icon className="w-3.5 h-3.5" />
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: textPrimary }}>{category}</p>
              <ul className="space-y-2">
                {links.map(link => (
                  <li key={link.label}>
                    <a href={link.href} className="text-xs transition-colors" style={{ color: textMuted }}
                      onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.color = '#94A3B8'; }}
                      onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.color = textMuted; }}>
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3" style={{ borderTop: `1px solid ${borderColor}` }}>
          <p className="text-xs" style={{ color: textMuted }}>© 2026 AgentFlow AI. All rights reserved.</p>
          <p className="text-xs" style={{ color: textMuted }}>
            Built with ❤️ by <span style={{ color: '#6366F1' }}>Aswin Kumar</span> · Final Year Project
          </p>
        </div>
      </div>
    </footer>
  );
}
