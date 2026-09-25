import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertCircle, Info, X, AlertTriangle } from 'lucide-react';

/* ─── Types ──────────────────────────────────────────────── */
export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
}

interface ToastContextValue {
  toasts: Toast[];
  toast: (opts: Omit<Toast, 'id'>) => void;
  dismiss: (id: string) => void;
}

/* ─── Context ────────────────────────────────────────────── */
const ToastContext = createContext<ToastContextValue | undefined>(undefined);

const ICONS: Record<ToastType, React.FC<React.SVGProps<SVGSVGElement>>> = {
  success: CheckCircle,
  error:   AlertCircle,
  info:    Info,
  warning: AlertTriangle,
};

const COLORS: Record<ToastType, { bg: string; icon: string; border: string }> = {
  success: { bg: 'rgba(34,197,94,0.08)',  icon: '#22C55E', border: 'rgba(34,197,94,0.2)'  },
  error:   { bg: 'rgba(239,68,68,0.08)',  icon: '#EF4444', border: 'rgba(239,68,68,0.2)'  },
  info:    { bg: 'rgba(99,102,241,0.08)', icon: '#6366F1', border: 'rgba(99,102,241,0.2)' },
  warning: { bg: 'rgba(245,158,11,0.08)', icon: '#F59E0B', border: 'rgba(245,158,11,0.2)' },
};

/* ─── Provider ───────────────────────────────────────────── */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const toast = useCallback((opts: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const newToast: Toast = { duration: 4000, ...opts, id };
    setToasts(prev => [newToast, ...prev].slice(0, 5));
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => dismiss(id), newToast.duration);
    }
  }, [dismiss]);

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
      {/* ── Toast Stack ─────────────────────────────────── */}
      <div
        style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 9999, display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'flex-end', pointerEvents: 'none' }}
      >
        <AnimatePresence initial={false}>
          {toasts.map(t => {
            const Icon = ICONS[t.type];
            const c    = COLORS[t.type];
            return (
              <motion.div
                key={t.id}
                layout
                initial={{ opacity: 0, y: 20, scale: 0.92 }}
                animate={{ opacity: 1, y: 0,  scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.92 }}
                transition={{ type: 'spring', stiffness: 320, damping: 28 }}
                style={{
                  pointerEvents: 'auto',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 10,
                  padding: '12px 14px',
                  borderRadius: 14,
                  width: 340,
                  backgroundColor: 'var(--surface)',
                  border: `1px solid ${c.border}`,
                  boxShadow: '0 8px 32px rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.15)',
                  backdropFilter: 'blur(12px)',
                }}
              >
                <div style={{ width: 28, height: 28, borderRadius: 8, backgroundColor: c.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1 }}>
                  <Icon style={{ width: 14, height: 14, color: c.icon }} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', margin: 0, lineHeight: 1.3 }}>{t.title}</p>
                  {t.description && (
                    <p style={{ fontSize: 11.5, color: 'var(--text-5)', margin: '3px 0 0', lineHeight: 1.5 }}>{t.description}</p>
                  )}
                </div>
                <button
                  onClick={() => dismiss(t.id)}
                  style={{ width: 20, height: 20, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'var(--text-5)', background: 'transparent', border: 'none', cursor: 'pointer', marginTop: 1 }}
                  onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--card)')}
                  onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <X style={{ width: 12, height: 12 }} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

/* ─── Hook ───────────────────────────────────────────────── */
export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside ToastProvider');
  return ctx;
}
