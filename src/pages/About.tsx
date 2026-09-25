import { motion } from 'framer-motion';
import { Zap, Code2, Globe, BookOpen, MessageSquare } from 'lucide-react';
import { Card } from '../components/ui/card';

const techStack = [
  { name: 'React 19', desc: 'UI framework', color: '#61DAFB' },
  { name: 'TypeScript', desc: 'Type safety', color: '#3178C6' },
  { name: 'Vite 8', desc: 'Build tool', color: '#646CFF' },
  { name: 'Tailwind CSS v4', desc: 'Utility styles', color: '#38BDF8' },
  { name: 'Framer Motion', desc: 'Animations', color: '#FF4D9E' },
  { name: 'React Router v7', desc: 'Routing', color: '#F44250' },
  { name: 'shadcn/ui', desc: 'UI primitives', color: '#F8FAFC' },
  { name: 'FastAPI (coming)', desc: 'Backend API', color: '#009688' },
  { name: 'Recharts', desc: 'Data visualization', color: '#22C55E' },
  { name: 'Zod', desc: 'Validation', color: '#6366F1' },
];

export default function About() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <Card glow className="p-8 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-[#6366F1]/10 via-transparent to-[#8B5CF6]/10 pointer-events-none" />
          <div className="absolute -right-20 -top-20 w-64 h-64 bg-[#6366F1]/10 rounded-full blur-3xl" />
          <div className="relative">
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center mx-auto mb-5 shadow-2xl shadow-[#6366F1]/40">
              <Zap className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-[var(--text)] mb-2">
              AgentFlow <span className="gradient-text">AI</span>
            </h1>
            <p className="text-[var(--text-4)] max-w-md mx-auto mb-4 text-sm leading-relaxed font-medium">
              An intelligent API workflow automation platform that lets you describe automations in plain English and deploy them instantly — powered by multi-agent AI.
            </p>
            <div className="inline-flex items-center gap-2 text-xs text-[var(--text-4)] bg-[var(--card)] border border-[var(--border-glass)] px-3 py-1.5 rounded-full font-medium">
              <span className="w-1.5 h-1.5 bg-[#22C55E] rounded-full animate-pulse" />
              Version 2.4.0 · Enterprise AI Studio
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Tech stack */}
      <div>
        <h3 className="text-sm font-bold text-[var(--text)] mb-4">Tech Stack</h3>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {techStack.map((tech, i) => (
            <motion.div key={tech.name} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.04 }}>
              <Card hover className="p-3 text-center glass-panel">
                <div className="w-2 h-2 rounded-full mx-auto mb-2" style={{ backgroundColor: tech.color }} />
                <p className="text-xs font-bold text-[var(--text)]">{tech.name}</p>
                <p className="text-[10px] text-[var(--text-4)] font-medium mt-0.5">{tech.desc}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Author */}
      <Card className="p-6 glass-panel">
        <h3 className="text-sm font-bold text-[var(--text)] mb-4">Built by</h3>
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center text-white font-bold text-xl shadow-lg">A</div>
          <div>
            <p className="font-bold text-[var(--text)]">Aswin Kumar</p>
            <p className="text-xs text-[var(--text-4)] font-medium mt-0.5">Enterprise AI Engineer · 2026</p>
            <p className="text-xs text-[#6366F1] font-semibold mt-1">AgentFlow AI — Intelligent API Workflow Automation</p>
          </div>
        </div>
      </Card>

      {/* Links */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Documentation', icon: BookOpen },
          { label: 'GitHub', icon: Code2 },
          { label: 'Community', icon: MessageSquare },
          { label: 'Status', icon: Globe },
        ].map(link => {
          const Icon = link.icon;
          return (
            <a key={link.label} href="#" className="flex items-center gap-2.5 p-3.5 rounded-xl border border-[var(--border-glass)] bg-[var(--card)] hover:border-[#6366F1]/40 hover:bg-indigo-500/10 text-[var(--text-4)] hover:text-[var(--text)] transition-all duration-200 group font-semibold">
              <Icon className="w-4 h-4 group-hover:text-[#6366F1] transition-colors" />
              <span className="text-sm">{link.label}</span>
            </a>
          );
        })}
      </div>
    </div>
  );
}
