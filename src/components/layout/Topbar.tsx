import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Search, Bell, Moon, Sun, ChevronRight, Menu, X, Sparkles, LogOut, User, Layers, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../context/ThemeContext';
import { useToast } from '../../context/ToastContext';
import { useAuthStore } from '../../store/useAuthStore';
import { Avatar, AvatarFallback } from '../ui/avatar';
import { Button } from '../ui/button';
import { CommandPalette } from './CommandPalette';
import { mockNotifications } from '../../data/mockData';
import { cn } from '../../lib/utils';

const pageMeta: Record<string, { crumbs: string[] }> = {
  '/dashboard':    { crumbs: ['Home', 'Overview'] },
  '/workflows':    { crumbs: ['Home', 'Workflows'] },
  '/builder':      { crumbs: ['Home', 'Workflow Builder'] },
  '/templates':    { crumbs: ['Home', 'Templates Workspace'] },
  '/discovery':    { crumbs: ['Home', 'API Intelligence'] },
  '/marketplace':  { crumbs: ['Home', 'AI Marketplace'] },
  '/connectors':   { crumbs: ['Home', 'Connectors Workspace'] },
  '/engine':       { crumbs: ['Home', 'Execution Engine'] },
  '/error-replay': { crumbs: ['Home', 'Error Replay'] },
  '/history':      { crumbs: ['Home', 'Execution History'] },
  '/analytics':    { crumbs: ['Home', 'Analytics'] },
  '/settings':     { crumbs: ['Home', 'Settings'] },
  '/profile':      { crumbs: ['Home', 'Profile'] },
  '/about':        { crumbs: ['Home', 'Documentation'] },
};

const notifTypeStyle: Record<string, string> = {
  error:   'text-[#EF4444] bg-[#EF4444]/10',
  success: 'text-[#22C55E] bg-[#22C55E]/10',
  warning: 'text-[#F59E0B] bg-[#F59E0B]/10',
  info:    'text-[#6366F1] bg-[#6366F1]/10',
};

interface TopbarProps {
  onOpenCommandPalette?: () => void;
  onOpenMobileMenu?: () => void;
  mobileMenuOpen?: boolean;
}

export function Topbar({ onOpenCommandPalette, onOpenMobileMenu, mobileMenuOpen }: TopbarProps) {
  const navigate                    = useNavigate();
  const { resolvedTheme, setTheme } = useTheme();
  const { toast }                   = useToast();
  const { user, logout }            = useAuthStore();
  const [notifOpen, setNotifOpen]   = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef                  = useRef<HTMLDivElement>(null);
  const [notifs, setNotifs]         = useState(mockNotifications);
  const [internalCmdOpen, setInternalCmdOpen] = useState(false);

  const location                    = useLocation();
  const meta                        = pageMeta[location.pathname] ?? { crumbs: ['Home', 'Workspace'] };
  const unread                      = notifs.filter(n => !n.read).length;

  const handleOpenSearch = () => {
    if (onOpenCommandPalette) {
      onOpenCommandPalette();
    } else {
      setInternalCmdOpen(true);
    }
  };

  // Profile Dropdown Outside Click & Escape key handler
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setProfileOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // Keyboard shortcut (Ctrl+K or Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        handleOpenSearch();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onOpenCommandPalette]);

  const handleNavigateSettings = () => {
    setProfileOpen(false);
    navigate('/settings');
  };

  const handleNavigateConnectors = () => {
    setProfileOpen(false);
    navigate('/connectors');
  };

  const handleSignOut = () => {
    setProfileOpen(false);
    logout();
    navigate('/login');
  };

  const markAllRead = () => {
    setNotifs(prev => prev.map(n => ({ ...n, read: true })));
    setNotifOpen(false);
    toast({ type: 'success', title: 'All notifications marked as read' });
  };

  return (
    <>
      <header className="h-16 shrink-0 flex items-center justify-between gap-4 px-6 relative z-30 bg-[#13102A]/90 backdrop-blur-md border-b border-[rgba(255,255,255,0.12)] text-white shadow-sm">
        
        {/* ── LEFT: Mobile Menu Button + Breadcrumbs ── */}
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={onOpenMobileMenu}
            className="md:hidden flex items-center justify-center w-9 h-9 rounded-xl transition-colors hover:bg-[#231E3A] text-[rgba(255,255,255,0.7)]"
            aria-label="Toggle menu"
          >
            <AnimatePresence mode="wait" initial={false}>
              {mobileMenuOpen ? (
                <motion.span key="close" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.13 }}>
                  <X className="w-4.5 h-4.5" />
                </motion.span>
              ) : (
                <motion.span key="menu" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.13 }}>
                  <Menu className="w-4.5 h-4.5" />
                </motion.span>
              )}
            </AnimatePresence>
          </button>

          {/* Breadcrumb Navigation */}
          <div className="hidden md:flex items-center gap-2 text-xs font-semibold min-w-0">
            {meta.crumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-2">
                {i > 0 && <ChevronRight className="w-3.5 h-3.5 text-[rgba(255,255,255,0.35)]" />}
                <span className={cn(i === meta.crumbs.length - 1 ? 'text-white font-extrabold' : 'text-[rgba(255,255,255,0.45)]')}>
                  {crumb}
                </span>
              </span>
            ))}
          </div>
        </div>

        {/* ── CENTER: Global Search Bar ── */}
        <div className="flex-1 max-w-[380px] mx-2">
          <button
            onClick={handleOpenSearch}
            className="w-full h-10 px-3.5 rounded-xl bg-[#1B1728]/90 border border-[rgba(255,255,255,0.12)] hover:border-[#FF6D00]/50 hover:bg-[#231E3A] focus:outline-none focus:ring-2 focus:ring-[#FF6D00]/40 focus:border-[#FF6D00] shadow-[inset_0_1px_2px_rgba(0,0,0,0.4)] transition-all duration-200 flex items-center justify-between gap-3 group backdrop-blur-md"
            title="Global Search (Ctrl + K)"
          >
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <Search className="w-4 h-4 text-[rgba(255,255,255,0.45)] group-hover:text-[#FF6D00] transition-colors shrink-0" />
              <span className="text-xs text-[rgba(255,255,255,0.45)] group-hover:text-white transition-colors truncate text-left">
                Search workflows, agents, specs...
              </span>
            </div>
            <span className="hidden sm:flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-[rgba(255,255,255,0.06)] text-[rgba(255,255,255,0.5)] border border-[rgba(255,255,255,0.08)] shrink-0">
              Ctrl + K
            </span>
          </button>
        </div>

        {/* ── RIGHT: Theme Toggle, Notifications, Profile & Logout ── */}
        <div className="flex items-center gap-3 justify-end shrink-0">

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            className="w-9 h-9 rounded-xl hover:bg-[#231E3A] text-[rgba(255,255,255,0.7)] hover:text-white transition"
            onClick={() => {
              const next = resolvedTheme === 'dark' ? 'light' : 'dark';
              setTheme(next);
              toast({ type: 'info', title: `Switched to ${next} mode`, duration: 2000 });
            }}
            aria-label="Toggle theme"
            title="Toggle Theme"
          >
            <AnimatePresence mode="wait" initial={false}>
              {resolvedTheme === 'dark' ? (
                <motion.span key="moon" initial={{ rotate: -90, opacity: 0, scale: 0.7 }} animate={{ rotate: 0, opacity: 1, scale: 1 }} exit={{ rotate: 90, opacity: 0, scale: 0.7 }} transition={{ duration: 0.15 }}>
                  <Moon className="w-4 h-4 text-[#FF6D00]" />
                </motion.span>
              ) : (
                <motion.span key="sun" initial={{ rotate: 90, opacity: 0, scale: 0.7 }} animate={{ rotate: 0, opacity: 1, scale: 1 }} exit={{ rotate: 90, opacity: 0, scale: 0.7 }} transition={{ duration: 0.15 }}>
                  <Sun className="w-4 h-4 text-amber-500" />
                </motion.span>
              )}
            </AnimatePresence>
          </Button>

          {/* Notifications */}
          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              className="w-9 h-9 rounded-xl hover:bg-[#231E3A] text-[rgba(255,255,255,0.7)] hover:text-white relative transition"
              onClick={() => setNotifOpen(v => !v)}
              aria-label="Notifications"
              title="Notifications"
            >
              <Bell className="w-4 h-4 text-white" />
              {unread > 0 && (
                <motion.span
                  initial={{ scale: 0 }} animate={{ scale: 1 }}
                  className="absolute top-2 right-2 w-2 h-2 bg-[#FF6D00] rounded-full ring-2 ring-[#0E0918] shadow-[0_0_8px_rgba(255,109,0,0.8)]"
                />
              )}
            </Button>

            <AnimatePresence>
              {notifOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setNotifOpen(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: 6, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 6, scale: 0.97 }}
                    transition={{ duration: 0.12 }}
                    className="absolute right-0 top-full mt-2 w-84 rounded-2xl shadow-2xl z-50 overflow-hidden bg-[#1B1728]/95 backdrop-blur-2xl border border-[rgba(255,255,255,0.12)] text-white"
                  >
                    <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(255,255,255,0.12)]">
                      <span className="text-xs font-bold text-white flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-[#FF6D00]" /> Notifications
                      </span>
                      {unread > 0 && (
                        <span className="text-[10px] font-semibold text-[#FF6D00] bg-[#FF6D00]/15 px-2 py-0.5 rounded-full border border-[#FF6D00]/30">
                          {unread} new
                        </span>
                      )}
                    </div>

                    <div className="max-h-64 overflow-y-auto">
                      {notifs.map(n => (
                        <div
                          key={n.id}
                          className={cn(
                            'px-4 py-3 border-b border-[rgba(255,255,255,0.08)] hover:bg-[#231E3A] transition-colors cursor-pointer flex items-start gap-3',
                            !n.read && 'bg-[#FF6D00]/5'
                          )}
                        >
                          <div className={cn('w-6 h-6 rounded-lg flex items-center justify-center shrink-0 mt-0.5 text-[10px] font-bold', notifTypeStyle[n.type])}>
                            {n.type === 'error' ? '✕' : n.type === 'success' ? '✓' : n.type === 'warning' ? '!' : 'i'}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-white leading-tight">{n.title}</p>
                            <p className="text-[11px] text-[rgba(255,255,255,0.50)] mt-0.5 line-clamp-2 leading-relaxed">{n.message}</p>
                          </div>
                          {!n.read && <div className="w-1.5 h-1.5 rounded-full bg-[#FF6D00] shrink-0 mt-1.5" />}
                        </div>
                      ))}
                    </div>

                    <button
                      onClick={markAllRead}
                      className="w-full py-2.5 text-xs font-semibold text-[#FF6D00] hover:text-[#FF802C] hover:bg-[#231E3A] transition-colors border-t border-[rgba(255,255,255,0.12)]"
                    >
                      Mark all as read
                    </button>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>

          <div className="h-5 w-px bg-[rgba(255,255,255,0.12)] mx-1 hidden sm:block" />

          {/* ── Profile & Account Dropdown ── */}
          <div className="relative" ref={profileRef}>
            <button
              type="button"
              onClick={() => setProfileOpen((v) => !v)}
              className="flex items-center gap-2.5 p-1 rounded-xl hover:bg-[#231E3A] border border-transparent hover:border-[rgba(255,255,255,0.1)] transition-all group"
              aria-expanded={profileOpen}
              aria-label="User profile menu"
            >
              <Avatar className="w-9 h-9 cursor-pointer border border-[rgba(255,255,255,0.15)] group-hover:border-[#FF6D00]/80 group-hover:shadow-[0_0_12px_rgba(255,109,0,0.4)] transition-all">
                <AvatarFallback className="bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] text-black text-xs font-extrabold">
                  {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'A'}
                </AvatarFallback>
              </Avatar>
              <div className="hidden lg:block text-left">
                <p className="text-xs font-bold text-white leading-tight group-hover:text-[#FF6D00] transition-colors">
                  {user?.full_name || 'Aswin Kumaar'}
                </p>
                <p className="text-[10px] text-[rgba(255,255,255,0.45)] mt-0.5">
                  {user?.email || 'aswin@agentflow.ai'}
                </p>
              </div>
              <ChevronDown className={cn("w-3.5 h-3.5 text-[rgba(255,255,255,0.5)] transition-transform duration-200 ml-0.5", profileOpen && "rotate-180 text-[#FF6D00]")} />
            </button>

            <AnimatePresence>
              {profileOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 6, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 6, scale: 0.97 }}
                  transition={{ duration: 0.12 }}
                  className="absolute right-0 top-full mt-2 w-56 rounded-2xl shadow-2xl z-50 overflow-hidden bg-[#1B1728]/95 backdrop-blur-2xl border border-[rgba(255,255,255,0.12)] text-white p-2 space-y-1"
                >
                  <div className="px-3 py-2.5 border-b border-[rgba(255,255,255,0.08)] mb-1">
                    <p className="text-xs font-bold text-white truncate">
                      {user?.full_name || 'Aswin Kumaar'}
                    </p>
                    <p className="text-[10px] text-[rgba(255,255,255,0.45)] truncate mt-0.5">
                      {user?.email || 'aswin@agentflow.ai'}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={handleNavigateSettings}
                    className="w-full px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-2.5 text-[rgba(255,255,255,0.8)] hover:text-white hover:bg-[#FF6D00]/15 hover:border-[#FF6D00]/30 border border-transparent transition-all"
                  >
                    <User className="w-4 h-4 text-[#FF6D00]" />
                    <span>Profile & Account</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleNavigateConnectors}
                    className="w-full px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-2.5 text-[rgba(255,255,255,0.8)] hover:text-white hover:bg-[#FF6D00]/15 hover:border-[#FF6D00]/30 border border-transparent transition-all"
                  >
                    <Layers className="w-4 h-4 text-[#FF6D00]" />
                    <span>Connectors</span>
                  </button>

                  <div className="h-px bg-[rgba(255,255,255,0.08)] my-1" />

                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="w-full px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-2.5 text-rose-400 hover:text-rose-300 hover:bg-rose-500/15 border border-transparent hover:border-rose-500/30 transition-all"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </header>

      <CommandPalette open={internalCmdOpen} onClose={() => setInternalCmdOpen(false)} />
    </>
  );
}
