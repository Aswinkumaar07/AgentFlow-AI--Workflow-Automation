import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Sparkles, ArrowRight, Play, Cpu, ShieldCheck, Zap } from 'lucide-react';
import { useLandingTheme } from '../../context/LandingThemeContext';
import { useState, useEffect, useRef } from 'react';

/* ─── Typing animation hook ─────────────────────────────────── */
const TYPED_WORDS = ['API Workflows', 'AI Automations', 'Smart Pipelines', 'Agent Networks'];

function useTypingEffect(words: string[], speed = 60, pause = 1800) {
  const [wordIdx, setWordIdx]   = useState(0);
  const [charIdx, setCharIdx]   = useState(0);
  const [deleting, setDeleting] = useState(false);
  const [display, setDisplay]   = useState('');

  useEffect(() => {
    const current = words[wordIdx];
    let timeout: ReturnType<typeof setTimeout>;

    if (!deleting && charIdx <= current.length) {
      timeout = setTimeout(() => {
        setDisplay(current.slice(0, charIdx));
        setCharIdx(c => c + 1);
      }, speed);
    } else if (!deleting && charIdx > current.length) {
      timeout = setTimeout(() => setDeleting(true), pause);
    } else if (deleting && charIdx >= 0) {
      timeout = setTimeout(() => {
        setDisplay(current.slice(0, charIdx));
        setCharIdx(c => c - 1);
      }, speed / 2);
    } else {
      setDeleting(false);
      setWordIdx(w => (w + 1) % words.length);
      setCharIdx(0);
    }
    return () => clearTimeout(timeout);
  }, [charIdx, deleting, wordIdx, words, speed, pause]);

  return display;
}

/* ─── Floating particles ────────────────────────────────────── */
const PARTICLES = Array.from({ length: 30 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: Math.random() * 2.5 + 1,
  dur: `${Math.random() * 6 + 5}s`,
  delay: `${Math.random() * 6}s`,
  color: ['#6366F1', '#8B5CF6', '#06B6D4', '#6366F1', '#A855F7'][i % 5],
  opacity: Math.random() * 0.45 + 0.2,
}));

/* ─── SVG workflow illustration nodes ───────────────────────── */
const nodes = [
  { id: 1, x: 80,  y: 160, label: 'Webhook Trigger', icon: '⚡', color: '#6366F1', delay: 0    },
  { id: 2, x: 260, y: 80,  label: 'AI Planner',       icon: '🧠', color: '#8B5CF6', delay: 0.15 },
  { id: 3, x: 440, y: 140, label: 'API Executor',     icon: '🔗', color: '#06B6D4', delay: 0.3  },
  { id: 4, x: 260, y: 250, label: 'Validator',        icon: '✅', color: '#22C55E', delay: 0.45 },
  { id: 5, x: 600, y: 200, label: 'Output',           icon: '📤', color: '#8B5CF6', delay: 0.6  },
];

const edges = [
  { x1: 140, y1: 175, x2: 275, y2: 110, delay: 0.4,  from: 1, to: 2 },
  { x1: 320, y1: 100, x2: 455, y2: 150, delay: 0.55, from: 2, to: 3 },
  { x1: 140, y1: 185, x2: 275, y2: 262, delay: 0.55, from: 1, to: 4 },
  { x1: 500, y1: 165, x2: 615, y2: 210, delay: 0.7,  from: 3, to: 5 },
  { x1: 320, y1: 262, x2: 615, y2: 220, delay: 0.7,  from: 4, to: 5 },
];

function WorkflowNode({ node, nodeBg, edgeColor, isActive }: { node: typeof nodes[0]; nodeBg: string; edgeColor: string; isActive: boolean }) {
  return (
    <motion.g
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: isActive ? 1.08 : 1 }}
      transition={{ duration: 0.4, delay: node.delay }}
    >
      {/* Execution Ring when active */}
      {isActive && (
        <circle cx={node.x + 48} cy={node.y + 28} r="42" fill="none" stroke="#22C55E" strokeWidth="2.5" className="active-exec-node" />
      )}
      <circle cx={node.x + 48} cy={node.y + 28} r="38" fill="none"
        stroke={isActive ? '#22C55E' : node.color} strokeOpacity="0.3" strokeWidth="1" />
      <rect x={node.x} y={node.y} width="96" height="56" rx="14" fill={nodeBg}
        stroke={isActive ? '#22C55E' : node.color} strokeOpacity={isActive ? 0.9 : 0.55} strokeWidth={isActive ? 2 : 1.5} />
      <text x={node.x + 18} y={node.y + 34} fontSize="18">{node.icon}</text>
      <text x={node.x + 40} y={node.y + 28} fontSize="9.5" fill={edgeColor} fontFamily="Inter" fontWeight="600">{node.label}</text>
      <rect x={node.x} y={node.y} width="4" height="56" rx="2" fill={isActive ? '#22C55E' : node.color} fillOpacity="0.85" />
    </motion.g>
  );
}

/* ─── Component ─────────────────────────────────────────────── */
export function HeroSection() {
  const { theme }  = useLandingTheme();
  const isDark     = theme === 'dark';
  const typedText  = useTypingEffect(TYPED_WORDS);
  const cardRef    = useRef<HTMLDivElement>(null);

  /* 2. Step-by-Step Live Execution Simulator */
  const [activeNodeIdx, setActiveNodeIdx] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveNodeIdx(prev => (prev + 1) % nodes.length);
    }, 1400);
    return () => clearInterval(timer);
  }, []);

  const textPrimary  = isDark ? '#F8FAFC'              : '#0F172A';
  const textMuted    = isDark ? '#94A3B8'              : '#64748B';
  const cardBg       = isDark ? 'rgba(24,24,27,0.85)'   : 'rgba(255,255,255,0.95)';
  const cardBorder   = isDark ? 'rgba(99,102,241,0.25)' : '#E2E8F0';
  const nodeBg       = isDark ? '#18181B'              : '#FFFFFF';
  const edgeColor    = isDark ? '#F8FAFC'              : '#334155';
  const edgeStroke   = isDark ? '#27272A'              : '#CBD5E1';
  const sectionBg    = isDark ? '#09090B'              : '#F8FAFC';

  /* 1. Cursor Spotlight & 3D Tilt Handler */
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    cardRef.current.style.setProperty('--mouse-x', `${x}px`);
    cardRef.current.style.setProperty('--mouse-y', `${y}px`);

    /* 3D Tilt calculations */
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = (-(y - centerY) / centerY) * 6; // max 6 deg
    const rotateY = ((x - centerX) / centerX) * 6;   // max 6 deg
    cardRef.current.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
  };

  const handleMouseLeave = () => {
    if (cardRef.current) {
      cardRef.current.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
    }
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16"
      style={{ backgroundColor: sectionBg }}>

      {/* ── Aurora glow ambient background ─────────────────── */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="aurora-orb-1 absolute"
          style={{ width: 750, height: 750, borderRadius: '50%', top: '-18%', left: '-10%',
            background: 'radial-gradient(circle, rgba(99,102,241,0.25) 0%, rgba(99,102,241,0.08) 45%, transparent 70%)',
            filter: 'blur(52px)',
          }} />
        <div className="aurora-orb-2 absolute"
          style={{ width: 650, height: 650, borderRadius: '50%', top: '8%', right: '-8%',
            background: 'radial-gradient(circle, rgba(139,92,246,0.22) 0%, rgba(139,92,246,0.06) 50%, transparent 70%)',
            filter: 'blur(58px)',
          }} />
        <div className="aurora-orb-3 absolute"
          style={{ width: 550, height: 550, borderRadius: '50%', bottom: '2%', left: '32%',
            background: 'radial-gradient(circle, rgba(6,182,212,0.16) 0%, rgba(99,102,241,0.06) 50%, transparent 70%)',
            filter: 'blur(64px)',
          }} />
      </div>

      {/* ── Floating particles ───────────────────────────────── */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {PARTICLES.map(p => (
          <div
            key={p.id}
            className="float-particle absolute rounded-full"
            style={{
              left: `${p.x}%`, top: `${p.y}%`,
              width: p.size, height: p.size,
              backgroundColor: p.color,
              opacity: p.opacity,
              boxShadow: `0 0 8px ${p.color}`,
              '--dur': p.dur, '--delay': p.delay,
            } as React.CSSProperties}
          />
        ))}
      </div>

      {/* ── Fine grid overlay ────────────────────────────────── */}
      <div className="absolute inset-0 opacity-[0.07] pointer-events-none" style={{
        backgroundImage: `linear-gradient(to right, #6366F1 1px, transparent 1px), linear-gradient(to bottom, #6366F1 1px, transparent 1px)`,
        backgroundSize: '64px 64px',
      }} />

      {/* ── Content ──────────────────────────────────────────── */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">

          {/* Left — headline */}
          <div>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mb-6">
              {/* 4. Shimmering Badge */}
              <span className="shimmer-badge inline-flex items-center gap-2 text-xs px-3.5 py-1.5 rounded-full font-semibold tracking-wide"
                style={{
                  backgroundColor: 'rgba(99,102,241,0.14)',
                  color: '#818CF8',
                  border: '1px solid rgba(99,102,241,0.35)',
                  boxShadow: '0 0 20px rgba(99,102,241,0.2)',
                }}>
                <Sparkles className="w-3.5 h-3.5 text-[#6366F1]" /> Powered by Multi-Agent AI Architecture
              </span>
            </motion.div>

            {/* Headline */}
            <motion.h1 initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.15] tracking-tight mb-6"
              style={{ color: textPrimary, fontFamily: 'var(--font-display)' }}>
              <span className="block">Build Intelligent</span>

              <span
                className="block overflow-hidden"
                style={{ height: '1.2em' }}
              >
                <span style={{
                  background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #06B6D4 100%)',
                  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
                  whiteSpace: 'nowrap',
                }}>
                  {typedText}
                </span>
                <span
                  className="animate-pulse"
                  style={{ WebkitTextFillColor: '#6366F1', color: '#6366F1', fontWeight: 300 }}
                >|</span>
              </span>

              <span className="block">Using AI Agents</span>
            </motion.h1>

            <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg leading-relaxed mb-8 max-w-lg" style={{ color: textMuted }}>
              Transform natural language into executable API workflows using Multi-Agent AI, RAG knowledge graph, self-correcting validation, and live visual monitoring.
            </motion.p>

            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-wrap gap-4">
              <Link to="/builder" onClick={() => localStorage.setItem('agentflow-token', 'demo-token')}>
                {/* 2. Border Beam Effect around CTA Button */}
                <div className="border-beam-container inline-block">
                  <div className="border-beam" />
                  <button className="relative z-10 flex items-center gap-2 px-7 py-3.5 rounded-xl font-semibold text-white transition-all shadow-lg"
                    style={{ background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)', boxShadow: '0 8px 28px rgba(99,102,241,0.45)' }}
                    onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-2px)'; (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 12px 34px rgba(99,102,241,0.6)'; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'none'; (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 8px 28px rgba(99,102,241,0.45)'; }}>
                    <Sparkles className="w-4 h-4 text-white" /> Get Started Free <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </Link>
              <button className="flex items-center gap-2 px-7 py-3.5 rounded-xl font-semibold transition-all"
                style={{ color: textPrimary, backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)', border: `1px solid ${cardBorder}`, backdropFilter: 'blur(8px)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = '#6366F1'; (e.currentTarget as HTMLButtonElement).style.color = '#6366F1'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = cardBorder; (e.currentTarget as HTMLButtonElement).style.color = textPrimary; }}>
                <Play className="w-4 h-4 text-[#6366F1]" /> Watch Demo
              </button>
            </motion.div>

            {/* Feature badges row */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.4 }}
              className="flex items-center gap-6 mt-8 pt-6 border-t" style={{ borderColor: isDark ? '#1F1F23' : '#E2E8F0' }}>
              <div className="flex items-center gap-2 text-xs font-medium" style={{ color: textMuted }}>
                <Cpu className="w-4 h-4 text-[#6366F1]" /> 4 Autonomous Agents
              </div>
              <div className="flex items-center gap-2 text-xs font-medium" style={{ color: textMuted }}>
                <ShieldCheck className="w-4 h-4 text-[#22C55E]" /> Self-Correcting DAG
              </div>
              <div className="flex items-center gap-2 text-xs font-medium" style={{ color: textMuted }}>
                <Zap className="w-4 h-4 text-[#F59E0B]" /> 200+ Connectors
              </div>
            </motion.div>
          </div>

          {/* Right — 1. 3D Tilt Card + 2. Live Execution Simulator */}
          <motion.div initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.7, delay: 0.2 }} className="relative">

            {/* Halo glow */}
            <div className="absolute inset-0 rounded-2xl blur-3xl opacity-35" style={{
              background: 'linear-gradient(135deg, rgba(99,102,241,0.55), rgba(139,92,246,0.4), rgba(6,182,212,0.25))',
              transform: 'scale(1.04)',
            }} />

            {/* 1. 3D Tilt & Cursor Spotlight Card */}
            <div
              ref={cardRef}
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
              className="spotlight-card relative rounded-2xl p-6 overflow-hidden"
              style={{
                backgroundColor: cardBg, border: `1px solid ${cardBorder}`,
                boxShadow: isDark ? '0 24px 64px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.08)' : '0 24px 64px rgba(0,0,0,0.1)',
                backdropFilter: 'blur(20px)',
              }}
            >
              {/* Window chrome */}
              <div className="flex items-center gap-2 mb-4 relative z-10">
                <div className="w-3 h-3 rounded-full bg-[#EF4444]" />
                <div className="w-3 h-3 rounded-full bg-[#F59E0B]" />
                <div className="w-3 h-3 rounded-full bg-[#22C55E]" />
                <span className="ml-2 text-xs font-medium" style={{ color: textMuted }}>workflow.agentflow.ai</span>
                {/* Live indicator */}
                <div className="ml-auto flex items-center gap-1.5">
                  <div className="relative w-2 h-2">
                    <div className="live-ping-ring absolute inset-0 rounded-full bg-[#22C55E] opacity-60" />
                    <div className="w-2 h-2 rounded-full bg-[#22C55E]" />
                  </div>
                  <span className="text-[10px] text-[#22C55E] font-semibold">Live Execution</span>
                </div>
              </div>

              {/* SVG with 2. Step-by-Step Live Execution Simulator & Edge Pulse Waves */}
              <svg viewBox="0 0 740 350" className="w-full relative z-10" style={{ height: 'auto', minHeight: 200 }}>
                {edges.map((edge, i) => (
                  <g key={i}>
                    {/* Base edge */}
                    <motion.line x1={edge.x1} y1={edge.y1} x2={edge.x2} y2={edge.y2}
                      stroke={edgeStroke} strokeWidth="1.5" strokeDasharray="6 4"
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: edge.delay }} />
                    {/* Animated Edge Pulse Wave */}
                    <line x1={edge.x1} y1={edge.y1} x2={edge.x2} y2={edge.y2}
                      stroke="#6366F1" strokeWidth="2.5" strokeOpacity="0.8" className="pulse-edge-path" />
                  </g>
                ))}
                {nodes.map((node, idx) => (
                  <WorkflowNode
                    key={node.id}
                    node={node}
                    nodeBg={nodeBg}
                    edgeColor={edgeColor}
                    isActive={activeNodeIdx === idx}
                  />
                ))}
              </svg>

              <div className="flex items-center justify-between mt-2 pt-3 relative z-10" style={{ borderTop: `1px solid ${cardBorder}` }}>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#22C55E] animate-pulse" />
                  <span className="text-xs text-[#22C55E] font-medium">
                    Step {activeNodeIdx + 1}/5: <span className="font-semibold text-white">{nodes[activeNodeIdx].label}</span>
                  </span>
                </div>
                <span className="text-xs" style={{ color: textMuted }}>1.2s · 2.8k tokens</span>
              </div>

              {/* Inner shimmer overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-[#6366F1]/10 via-transparent to-[#8B5CF6]/5 pointer-events-none rounded-2xl" />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
