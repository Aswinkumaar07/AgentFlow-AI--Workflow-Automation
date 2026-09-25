import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, LayoutDashboard, GitBranch, History, BarChart2,
  Settings, User, Zap, Moon, Sun, Play, Plus, HelpCircle,
  ArrowRight, Sparkles, FileText,
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useToast } from '../../context/ToastContext';

/* ─── Command registry ───────────────────────────────────── */
interface Cmd {
  id: string;
  label: string;
  description?: string;
  icon: React.FC<React.SVGProps<SVGSVGElement>>;
  color: string;
  group: string;
  action: 'navigate' | 'theme' | 'toast';
  payload?: string;
}

const BASE_COMMANDS: Cmd[] = [
  // Navigation
  { id: 'nav-dash',     label: 'Go to Dashboard',       description: 'Overview & metrics',         icon: LayoutDashboard, color: '#6366F1', group: 'Navigate', action: 'navigate', payload: '/dashboard' },
  { id: 'nav-builder',  label: 'Go to Workflow Builder', description: 'AI & manual workflow editor', icon: GitBranch,       color: '#8B5CF6', group: 'Navigate', action: 'navigate', payload: '/builder'   },
  { id: 'nav-history',  label: 'Go to History',          description: 'Execution logs',             icon: History,         color: '#06B6D4', group: 'Navigate', action: 'navigate', payload: '/history'   },
  { id: 'nav-analytics',label: 'Go to Analytics',        description: 'Charts & insights',          icon: BarChart2,       color: '#22C55E', group: 'Navigate', action: 'navigate', payload: '/analytics' },
  { id: 'nav-settings', label: 'Go to Settings',         description: 'Account & preferences',      icon: Settings,        color: '#F59E0B', group: 'Navigate', action: 'navigate', payload: '/settings'  },
  { id: 'nav-profile',  label: 'Go to Profile',          description: 'Your account',               icon: User,            color: '#EF4444', group: 'Navigate', action: 'navigate', payload: '/profile'   },
  // Actions
  { id: 'act-new',      label: 'New Workflow',           description: 'Open AI Builder',            icon: Plus,            color: '#6366F1', group: 'Actions',  action: 'navigate', payload: '/builder'   },
  { id: 'act-run',      label: 'Run Active Workflows',   description: 'Trigger all live workflows',  icon: Play,            color: '#22C55E', group: 'Actions',  action: 'toast',    payload: 'run'        },
  { id: 'act-ai',       label: 'Generate with AI',       description: 'Describe a workflow in natural language', icon: Sparkles, color: '#8B5CF6', group: 'Actions', action: 'navigate', payload: '/builder' },
  { id: 'act-export',   label: 'Export Workflows',       description: 'Download as JSON',           icon: FileText,        color: '#F59E0B', group: 'Actions',  action: 'toast',    payload: 'export'     },
  // Settings
  { id: 'set-dark',     label: 'Switch to Dark Mode',    description: 'Apply dark theme',           icon: Moon,            color: '#52525B', group: 'Settings', action: 'theme',    payload: 'dark'       },
  { id: 'set-light',    label: 'Switch to Light Mode',   description: 'Apply light theme',          icon: Sun,             color: '#F59E0B', group: 'Settings', action: 'theme',    payload: 'light'      },
  // Help
  { id: 'help-docs',    label: 'Documentation',          description: 'Open docs in new tab',       icon: HelpCircle,      color: '#06B6D4', group: 'Help',     action: 'toast',    payload: 'docs'       },
  { id: 'help-api',     label: 'API Reference',          description: 'Browse API endpoints',       icon: Zap,             color: '#6366F1', group: 'Help',     action: 'toast',    payload: 'api'        },
];

/* ─── Fuzzy filter ───────────────────────────────────────── */
function fuzzy(query: string, text: string): boolean {
  if (!query) return true;
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  if (t.includes(q)) return true;
  let qi = 0;
  for (const ch of t) {
    if (ch === q[qi]) qi++;
    if (qi === q.length) return true;
  }
  return false;
}

/* ─── Component ──────────────────────────────────────────── */
interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const [query, setQuery]     = useState('');
  const [active, setActive]   = useState(0);
  const navigate              = useNavigate();
  const { setTheme }          = useTheme();
  const { toast }             = useToast();
  const inputRef              = useRef<HTMLInputElement>(null);

  const filtered = BASE_COMMANDS.filter(c =>
    fuzzy(query, c.label) || fuzzy(query, c.description ?? '') || fuzzy(query, c.group)
  );

  // Group the results
  const groups = Array.from(new Set(filtered.map(c => c.group)));

  const executeCommand = useCallback((cmd: Cmd) => {
    onClose();
    setQuery('');
    if (cmd.action === 'navigate') {
      navigate(cmd.payload!);
    } else if (cmd.action === 'theme') {
      setTheme(cmd.payload as 'dark' | 'light');
      toast({ type: 'success', title: `${cmd.payload === 'dark' ? 'Dark' : 'Light'} mode enabled` });
    } else if (cmd.action === 'toast') {
      const msgs: Record<string, { title: string; description?: string; type: 'success'|'info' }> = {
        run:    { type: 'success', title: 'Workflows triggered', description: '8 active workflows are now running' },
        export: { type: 'success', title: 'Export started', description: 'workflows.json will download shortly' },
        docs:   { type: 'info',    title: 'Documentation', description: 'Opening AgentFlow docs in a new tab' },
        api:    { type: 'info',    title: 'API Reference', description: 'Opening API reference in a new tab' },
      };
      const m = msgs[cmd.payload!];
      if (m) toast(m);
    }
  }, [navigate, onClose, setTheme, toast]);

  // Keyboard nav
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActive(a => Math.min(a + 1, filtered.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActive(a => Math.max(a - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[active]) executeCommand(filtered[active]);
      } else if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, active, filtered, executeCommand, onClose]);

  // Reset on open/query
  useEffect(() => { setActive(0); }, [query, open]);
  useEffect(() => {
    if (open) { setTimeout(() => inputRef.current?.focus(), 30); setQuery(''); }
  }, [open]);

  // Flat index for active highlight
  let flatIdx = 0;

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)', zIndex: 999 }}
          />

          {/* Panel */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -16 }}
            transition={{ type: 'spring', stiffness: 380, damping: 30 }}
            style={{
              position: 'fixed',
              top: '18%',
              left: '50%',
              transform: 'translateX(-50%)',
              width: 'min(600px, 92vw)',
              zIndex: 1000,
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 18,
              boxShadow: '0 24px 64px rgba(0,0,0,0.4), 0 0 0 1px rgba(99,102,241,0.1)',
              overflow: 'hidden',
            }}
          >
            {/* Search bar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', borderBottom: '1px solid var(--border-sub)' }}>
              <Search style={{ width: 16, height: 16, color: 'var(--text-5)', flexShrink: 0 }} />
              <input
                ref={inputRef}
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search commands, pages, actions…"
                style={{
                  flex: 1, border: 'none', outline: 'none',
                  background: 'transparent', fontSize: 14,
                  color: 'var(--text)', caretColor: '#6366F1',
                }}
              />
              <kbd style={{ fontSize: 10, color: 'var(--text-6)', backgroundColor: 'var(--card)', border: '1px solid var(--border-sub)', borderRadius: 5, padding: '2px 6px', flexShrink: 0 }}>ESC</kbd>
            </div>

            {/* Results */}
            <div style={{ maxHeight: 420, overflowY: 'auto', padding: '6px 0' }}>
              {filtered.length === 0 ? (
                <div style={{ padding: '32px 16px', textAlign: 'center' }}>
                  <p style={{ fontSize: 13, color: 'var(--text-5)', margin: 0 }}>No commands found for "<span style={{ color: 'var(--text-3)' }}>{query}</span>"</p>
                </div>
              ) : (
                groups.map(group => {
                  const cmds = filtered.filter(c => c.group === group);
                  return (
                    <div key={group}>
                      <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--text-6)', padding: '8px 16px 4px' }}>{group}</p>
                      {cmds.map(cmd => {
                        const Icon = cmd.icon;
                        const isActive = flatIdx === active;
                        const currentIdx = flatIdx++;
                        return (
                          <button
                            key={cmd.id}
                            onClick={() => executeCommand(cmd)}
                            onMouseEnter={() => setActive(currentIdx)}
                            style={{
                              display: 'flex', alignItems: 'center', gap: 12,
                              width: '100%', padding: '9px 16px',
                              backgroundColor: isActive ? 'var(--card)' : 'transparent',
                              border: 'none', cursor: 'pointer', textAlign: 'left',
                              transition: 'background-color 0.1s',
                            }}
                          >
                            <div style={{ width: 30, height: 30, borderRadius: 8, backgroundColor: `${cmd.color}18`, border: `1px solid ${cmd.color}30`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                              <Icon style={{ width: 13, height: 13, color: cmd.color }} />
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)', margin: 0, lineHeight: 1.3 }}>{cmd.label}</p>
                              {cmd.description && (
                                <p style={{ fontSize: 11, color: 'var(--text-5)', margin: '1px 0 0', lineHeight: 1.4 }}>{cmd.description}</p>
                              )}
                            </div>
                            {isActive && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <kbd style={{ fontSize: 9.5, color: 'var(--text-6)', backgroundColor: 'var(--border-sub)', border: '1px solid var(--border)', borderRadius: 4, padding: '1px 5px' }}>↵ Enter</kbd>
                              </div>
                            )}
                            <ArrowRight style={{ width: 12, height: 12, color: 'var(--text-6)', opacity: isActive ? 1 : 0, flexShrink: 0 }} />
                          </button>
                        );
                      })}
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer hint */}
            <div style={{ borderTop: '1px solid var(--border-sub)', padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 16 }}>
              {[['↑↓', 'navigate'], ['↵', 'select'], ['esc', 'close']].map(([key, label]) => (
                <span key={key} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10.5, color: 'var(--text-6)' }}>
                  <kbd style={{ backgroundColor: 'var(--card)', border: '1px solid var(--border-sub)', borderRadius: 4, padding: '1px 5px', fontSize: 10 }}>{key}</kbd>
                  {label}
                </span>
              ))}
              <span style={{ marginLeft: 'auto', fontSize: 10.5, color: 'var(--text-6)' }}>{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
