import { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { CommandPalette } from './CommandPalette';

export function AppLayout() {
  const location                    = useLocation();
  const [cmdOpen, setCmdOpen]       = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Ctrl+K / Cmd+K to open command palette
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setCmdOpen(v => !v);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // Close mobile sidebar on route change
  useEffect(() => { setMobileOpen(false); }, [location.pathname]);

  return (
    <div className="flex h-screen overflow-hidden relative bg-[#0E0918] text-white">

      {/* ── Ambient Background Glow Layer ── */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        {/* Glow Orb 1 — Brand Orange (#FF6D00) */}
        <div className="absolute rounded-full" style={{
          width: 600, height: 600, top: '-15%', left: '10%',
          background: 'radial-gradient(circle, rgba(255, 109, 0, 0.10) 0%, transparent 70%)',
          filter: 'blur(90px)',
        }} />
        {/* Glow Orb 2 — Deep Red Orange (#FF0C00) */}
        <div className="absolute rounded-full" style={{
          width: 550, height: 550, bottom: '0%', right: '5%',
          background: 'radial-gradient(circle, rgba(255, 12, 0, 0.08) 0%, transparent 70%)',
          filter: 'blur(90px)',
        }} />
        {/* Glow Orb 3 — Subtle Violet AI Glow (#A855F7) */}
        <div className="absolute rounded-full" style={{
          width: 500, height: 500, top: '40%', right: '30%',
          background: 'radial-gradient(circle, rgba(168, 85, 247, 0.05) 0%, transparent 70%)',
          filter: 'blur(100px)',
        }} />

        {/* Fine Ambient Grid overlay */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{
          backgroundImage: `linear-gradient(to right, rgba(255, 109, 0, 0.4) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 109, 0, 0.4) 1px, transparent 1px)`,
          backgroundSize: '48px 48px',
        }} />
      </div>

      {/* ── Desktop sidebar ───────────────────────────────── */}
      <div className="hidden md:block relative z-30">
        <Sidebar />
      </div>

      {/* ── Mobile sidebar drawer ─────────────────────────── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
              onClick={() => setMobileOpen(false)}
              className="fixed inset-0 bg-[#0E0918]/85 backdrop-blur-md z-50"
            />
            {/* Drawer */}
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', stiffness: 320, damping: 30 }}
              className="fixed left-0 top-0 bottom-0 z-51"
            >
              <Sidebar />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden relative z-10">
        <Topbar
          onOpenCommandPalette={() => setCmdOpen(true)}
          onOpenMobileMenu={() => setMobileOpen(v => !v)}
          mobileMenuOpen={mobileOpen}
        />

        <main className="flex-1 overflow-y-auto">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="px-6 py-6 min-h-full"
          >
            <Outlet />
          </motion.div>
        </main>
      </div>

      {/* ── Command Palette ───────────────────────────────── */}
      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} />
    </div>
  );
}
