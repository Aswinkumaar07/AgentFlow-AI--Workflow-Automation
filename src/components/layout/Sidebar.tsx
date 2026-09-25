import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Workflow,
  LayoutTemplate,
  Cpu,
  Settings,
  Zap,
  Store,
  AlertOctagon,
  BarChart3,
  History,
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Workflows', path: '/workflows', icon: Workflow },
  { name: 'Templates', path: '/templates', icon: LayoutTemplate },
  { name: 'AI Marketplace', path: '/marketplace', icon: Store },
  { name: 'Connectors', path: '/connectors', icon: Cpu },
  { name: 'Execution Engine', path: '/engine', icon: Zap },
  { name: 'History', path: '/history', icon: History },
  { name: 'Error Replay', path: '/error-replay', icon: AlertOctagon },
  { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 border-r border-[rgba(255,255,255,0.12)] bg-[rgba(27,23,40,0.72)] backdrop-blur-[12px] text-white flex flex-col h-screen sticky top-0 shrink-0 z-30">
      {/* ── Sidebar Header ───────────────────────────────────── */}
      <div className="h-16 flex items-center gap-3 px-5 border-b border-[rgba(255,255,255,0.12)] shrink-0">
        <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] flex items-center justify-center text-white font-bold shadow-[0_4px_16px_rgba(255,109,0,0.40)]">
          <Zap className="h-5 w-5 fill-current" />
        </div>
        <div>
          <h1 className="font-bold text-base tracking-tight text-white leading-none">AgentFlow AI</h1>
          <span className="text-[10px] uppercase font-bold text-[#FF6D00] tracking-widest mt-1 block">Enterprise Platform</span>
        </div>
      </div>

      {/* ── Navigation List ──────────────────────────────────── */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        <div className="px-3 mb-2 text-[11px] font-semibold text-[rgba(255,255,255,0.45)] uppercase tracking-wider">
          Main Workspace
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 relative ${
                  isActive
                    ? 'bg-gradient-to-r from-[rgba(255,109,0,0.22)] to-[rgba(255,12,0,0.12)] text-white font-semibold border border-[rgba(255,109,0,0.35)] shadow-[0_4px_14px_rgba(255,109,0,0.18)]'
                    : 'text-[rgba(255,255,255,0.65)] hover:bg-[#231E3A] hover:text-white border border-transparent'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full bg-[#FF6D00] shadow-[0_0_10px_rgba(255,109,0,0.6)]" />
                  )}
                  <Icon className={`h-4 w-4 shrink-0 transition-colors ${isActive ? 'text-[#FF6D00]' : 'text-[rgba(255,255,255,0.50)]'}`} />
                  <span className="truncate">{item.name}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* ── Sidebar Footer ───────────────────────────────────── */}
      <div className="p-4 border-t border-[rgba(255,255,255,0.12)] bg-[#13102A]/60 text-xs flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#22C55E] animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
          <span className="text-[rgba(255,255,255,0.65)] text-[11px] font-medium">Systems Operational</span>
        </div>
        <span className="font-mono text-[10px] text-[rgba(255,255,255,0.45)] font-semibold px-2 py-0.5 rounded-md bg-[rgba(255,255,255,0.06)] border border-[rgba(255,255,255,0.08)]">v2.4-ent</span>
      </div>
    </aside>
  );
};
