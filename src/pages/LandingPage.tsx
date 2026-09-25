import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap,
  ArrowRight,
  Sparkles,
  Bot,
  Search,
  Workflow,
  Cpu,
  ShieldCheck,
  Activity,
  CheckCircle2,
  Mail,
  MessageSquare,
  GitBranch,
  FolderGit2,
  Globe,
  Lock,
  RefreshCw,
  Eye,
  Menu,
  X,
  FileCode2
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeDemoStep, setActiveDemoStep] = useState(0);

  const capabilities = [
    {
      icon: Sparkles,
      title: 'AI Workflow Generation',
      description: 'Describe what you need in plain English and automatically compile an executable multi-node DAG.'
    },
    {
      icon: Search,
      title: 'API Discovery',
      description: 'Automatically discover, index, and bind REST and OpenAPI endpoints to your workflow steps.'
    },
    {
      icon: Workflow,
      title: 'Visual DAG Builder',
      description: 'Refine workflow topology, edge connections, and parameters using an interactive canvas.'
    },
    {
      icon: Cpu,
      title: 'Multi-Service Automation',
      description: 'Orchestrate Google Workspace, Slack, GitHub, and custom REST APIs seamlessly.'
    },
    {
      icon: ShieldCheck,
      title: 'Human Approval',
      description: 'Pause execution dynamically for human review before performing critical operations.'
    },
    {
      icon: Activity,
      title: 'Execution Monitoring',
      description: 'Track workflow telemetry, detailed step logs, and automated self-healing error recovery.'
    }
  ];

  const connectorTools = [
    { name: 'Gmail', category: 'Communication', icon: Mail, color: 'text-red-400 bg-red-500/10 border-red-500/20' },
    { name: 'Slack', category: 'Messaging', icon: MessageSquare, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
    { name: 'GitHub', category: 'Developer Tools', icon: GitBranch, color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
    { name: 'Google Drive', category: 'Storage', icon: FolderGit2, color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
    { name: 'REST APIs', category: 'Custom Integrations', icon: Globe, color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
    { name: 'Notion', category: 'Productivity', icon: FileCode2, color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20' }
  ];

  const executionControls = [
    { title: 'DAG Validation', description: 'Compile-time structure and type checking before execution starts.', icon: CheckCircle2 },
    { title: 'Automated Retries', description: 'Configurable backoff strategies for transient network failures.', icon: RefreshCw },
    { title: 'Human-in-the-Loop', description: 'Interactive approval gates for sensitive actions.', icon: Lock },
    { title: 'Execution History', description: 'Complete step-by-step audit logs with payload inspection.', icon: Eye },
    { title: 'Live Telemetry', description: 'Real-time performance metrics and connector health scores.', icon: Activity }
  ];

  return (
    <div className="min-h-screen bg-[#0E0918] text-white selection:bg-[#FF6D00] selection:text-white relative overflow-hidden font-sans">
      {/* ── Ambient Background Orbs & Grid ──────────────────────────────── */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
        <div
          className="absolute rounded-full"
          style={{
            width: 700,
            height: 700,
            top: '-10%',
            left: '15%',
            background: 'radial-gradient(circle, rgba(255, 109, 0, 0.12) 0%, transparent 70%)',
            filter: 'blur(100px)'
          }}
        />
        <div
          className="absolute rounded-full"
          style={{
            width: 600,
            height: 600,
            top: '40%',
            right: '5%',
            background: 'radial-gradient(circle, rgba(255, 12, 0, 0.08) 0%, transparent 70%)',
            filter: 'blur(100px)'
          }}
        />
        <div
          className="absolute rounded-full"
          style={{
            width: 500,
            height: 500,
            bottom: '5%',
            left: '5%',
            background: 'radial-gradient(circle, rgba(168, 85, 247, 0.06) 0%, transparent 70%)',
            filter: 'blur(110px)'
          }}
        />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(to right, rgba(255, 109, 0, 0.4) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 109, 0, 0.4) 1px, transparent 1px)`,
            backgroundSize: '48px 48px'
          }}
        />
      </div>

      {/* ── Sticky Glass Navbar ─────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-[#1B1728]/75 backdrop-blur-[12px] border-b border-[rgba(255,255,255,0.12)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] flex items-center justify-center text-white font-bold shadow-[0_4px_16px_rgba(255,109,0,0.40)] group-hover:scale-105 transition-transform">
              <Zap className="h-5 w-5 fill-current" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-white block leading-none">AgentFlow AI</span>
              <span className="text-[10px] uppercase font-bold text-[#FF6D00] tracking-widest mt-1 block">Enterprise Platform</span>
            </div>
          </Link>

          {/* Nav Links — Desktop */}
          <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-[rgba(255,255,255,0.70)]">
            <a href="#product" className="hover:text-white transition-colors">Product</a>
            <a href="#features" className="hover:text-white transition-colors">Solutions</a>
            <a href="#developers" className="hover:text-white transition-colors">Developers</a>
            <a href="#capabilities" className="hover:text-white transition-colors">Resources</a>
          </nav>

          {/* Auth CTA Actions */}
          <div className="hidden md:flex items-center gap-4">
            <Link
              to="/login"
              className="text-xs font-semibold text-[rgba(255,255,255,0.85)] hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-[rgba(255,255,255,0.06)]"
            >
              Log in
            </Link>
            <Link
              to="/signup"
              className="text-xs font-semibold px-4 py-2 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-[0_4px_20px_rgba(255,109,0,0.35)] hover:shadow-[0_6px_24px_rgba(255,109,0,0.50)] hover:brightness-110 active:scale-[0.96] transition-all"
            >
              Get Started
            </Link>
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            onClick={() => setMobileMenuOpen(v => !v)}
            className="md:hidden p-2 rounded-lg text-[rgba(255,255,255,0.70)] hover:text-white hover:bg-[#231E3A]"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile Navigation Drawer */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-b border-[rgba(255,255,255,0.12)] bg-[#13102A]/95 backdrop-blur-xl px-4 py-6 space-y-4"
            >
              <nav className="flex flex-col space-y-3 text-sm font-semibold text-[rgba(255,255,255,0.80)]">
                <a href="#product" onClick={() => setMobileMenuOpen(false)} className="hover:text-[#FF6D00]">Product</a>
                <a href="#features" onClick={() => setMobileMenuOpen(false)} className="hover:text-[#FF6D00]">Solutions</a>
                <a href="#developers" onClick={() => setMobileMenuOpen(false)} className="hover:text-[#FF6D00]">Developers</a>
                <a href="#capabilities" onClick={() => setMobileMenuOpen(false)} className="hover:text-[#FF6D00]">Resources</a>
              </nav>
              <div className="pt-4 border-t border-[rgba(255,255,255,0.12)] flex flex-col gap-2">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 rounded-xl border border-[rgba(255,255,255,0.12)] text-sm font-semibold text-white bg-[#1B1728]"
                >
                  Log in
                </Link>
                <Link
                  to="/signup"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-sm font-semibold text-white shadow-lg"
                >
                  Get Started
                </Link>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* ── Hero Section ─────────────────────────────────────────────────── */}
      <section id="product" className="relative z-10 pt-20 pb-16 md:pt-28 md:pb-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#FF6D00]/15 border border-[#FF6D00]/30 text-[#FF9E43] text-xs font-semibold mb-6 shadow-[0_0_15px_rgba(255,109,0,0.15)]"
        >
          <Sparkles className="h-3.5 w-3.5 text-[#FF6D00]" />
          <span>Next-Generation Multi-Agent Orchestration</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-white max-w-5xl mx-auto leading-[1.1]"
        >
          Build AI-Powered Workflows.{' '}
          <span className="bg-gradient-to-r from-[#FF6D00] via-[#FF0C00] to-[#FF802C] bg-clip-text text-transparent">
            From Idea to Execution.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-6 text-base sm:text-lg md:text-xl text-[rgba(255,255,255,0.70)] max-w-3xl mx-auto leading-relaxed font-medium"
        >
          Turn natural-language requirements into intelligent, connected workflows that discover APIs, orchestrate services, and execute automatically.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            to="/signup"
            className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white font-bold text-base shadow-[0_4px_24px_rgba(255,109,0,0.40)] hover:shadow-[0_6px_32px_rgba(255,109,0,0.60)] hover:brightness-110 active:scale-[0.96] transition-all flex items-center justify-center gap-2"
          >
            Start Building <ArrowRight className="h-5 w-5" />
          </Link>
          <a
            href="#demo"
            className="w-full sm:w-auto px-8 py-4 rounded-xl bg-[#1B1728]/80 text-white border border-[rgba(255,255,255,0.12)] font-semibold text-base hover:bg-[#231E3A] hover:border-[#FF6D00]/40 transition-all flex items-center justify-center gap-2 backdrop-blur-md"
          >
            Explore Workflows
          </a>
        </motion.div>

        {/* ── Hero Animated Workflow Visualization ──────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-16 max-w-5xl mx-auto rounded-2xl bg-[#1B1728]/70 border border-[rgba(255,255,255,0.12)] p-6 md:p-8 backdrop-blur-2xl shadow-2xl relative overflow-hidden"
        >
          <div className="flex items-center justify-between pb-6 border-b border-[rgba(255,255,255,0.08)] mb-8">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500/80" />
              <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <span className="w-3 h-3 rounded-full bg-green-500/80" />
              <span className="ml-2 text-xs font-mono text-[rgba(255,255,255,0.45)]">agentflow-orchestrator.dag</span>
            </div>
            <div className="flex items-center gap-2 text-xs font-semibold text-[#FF9E43] bg-[#FF6D00]/15 px-3 py-1 rounded-full border border-[#FF6D00]/30">
              <Sparkles className="h-3.5 w-3.5 text-[#FF6D00]" /> AI Workflow Pipeline Active
            </div>
          </div>

          {/* Prompt Banner */}
          <div className="mb-8 bg-[#0E0918]/80 border border-[rgba(255,255,255,0.12)] rounded-xl p-4 flex items-center gap-3 text-left">
            <div className="p-2 rounded-lg bg-[#FF6D00]/20 text-[#FF6D00] shrink-0">
              <Bot className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-[10px] uppercase font-bold text-[rgba(255,255,255,0.45)] tracking-wider block">Natural Language Prompt</span>
              <p className="text-sm font-semibold text-white truncate">"Find my latest emails from LinkedIn, summarize them, and notify Slack."</p>
            </div>
          </div>

          {/* Interactive Visual Flow Steps */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
            {[
              { title: 'Natural Language', sub: 'Requirement Input', icon: Bot, step: '01' },
              { title: 'AI Planning', sub: 'Planner V4 Compiler', icon: Sparkles, step: '02' },
              { title: 'API Discovery', sub: 'Schema Binding', icon: Search, step: '03' },
              { title: 'Workflow DAG', sub: 'Topology Graph', icon: GitBranch, step: '04' },
              { title: 'Execution', sub: 'Automated Dispatch', icon: Activity, step: '05' }
            ].map((item, idx) => {
              const Icon = item.icon;
              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border text-left transition-all duration-300 relative ${
                    activeDemoStep === idx
                      ? 'bg-gradient-to-b from-[#FF6D00]/20 to-[#FF0C00]/10 border-[#FF6D00]/60 shadow-[0_0_20px_rgba(255,109,0,0.25)]'
                      : 'bg-[#13102A]/80 border-[rgba(255,255,255,0.08)] hover:border-[rgba(255,255,255,0.20)]'
                  }`}
                  onClick={() => setActiveDemoStep(idx)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono font-bold text-[#FF6D00]">{item.step}</span>
                    <Icon className={`h-4 w-4 ${activeDemoStep === idx ? 'text-[#FF6D00]' : 'text-[rgba(255,255,255,0.45)]'}`} />
                  </div>
                  <h4 className="text-xs font-bold text-white mb-0.5">{item.title}</h4>
                  <p className="text-[10px] text-[rgba(255,255,255,0.45)] font-medium">{item.sub}</p>
                </div>
              );
            })}
          </div>

          {/* Visual Execution Nodes Flow */}
          <div className="mt-8 pt-8 border-t border-[rgba(255,255,255,0.08)] grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3.5 rounded-xl bg-[#13102A] border border-[rgba(255,255,255,0.12)] flex items-center gap-3 text-left">
              <div className="p-2 rounded-lg bg-red-500/15 text-red-400 shrink-0">
                <Mail className="h-4 w-4" />
              </div>
              <div>
                <span className="text-xs font-bold text-white block">Gmail Search</span>
                <span className="text-[10px] text-[rgba(255,255,255,0.45)]">q: from:linkedin</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[#13102A] border border-[rgba(255,255,255,0.12)] flex items-center gap-3 text-left">
              <div className="p-2 rounded-lg bg-blue-500/15 text-blue-400 shrink-0">
                <Mail className="h-4 w-4" />
              </div>
              <div>
                <span className="text-xs font-bold text-white block">Gmail Get</span>
                <span className="text-[10px] text-[rgba(255,255,255,0.45)]">Fetch Message Body</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[#13102A] border border-[rgba(255,255,255,0.12)] flex items-center gap-3 text-left">
              <div className="p-2 rounded-lg bg-purple-500/15 text-purple-400 shrink-0">
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <span className="text-xs font-bold text-white block">AI Summarize</span>
                <span className="text-[10px] text-[rgba(255,255,255,0.45)]">LLM Key Findings</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[#13102A] border border-[rgba(255,255,255,0.12)] flex items-center gap-3 text-left">
              <div className="p-2 rounded-lg bg-emerald-500/15 text-emerald-400 shrink-0">
                <MessageSquare className="h-4 w-4" />
              </div>
              <div>
                <span className="text-xs font-bold text-white block">Slack Notify</span>
                <span className="text-[10px] text-[rgba(255,255,255,0.45)]">#general channel</span>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── Capability Strip ────────────────────────────────────────────── */}
      <section id="capabilities" className="py-16 bg-[#13102A]/50 border-y border-[rgba(255,255,255,0.08)] relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-xs font-bold uppercase tracking-widest text-[#FF6D00] mb-2">Core Platform Capabilities</h2>
            <p className="text-2xl sm:text-3xl font-extrabold text-white">Engineered for Enterprise Automation</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {capabilities.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div
                  key={idx}
                  className="p-6 rounded-2xl bg-[#1B1728]/80 border border-[rgba(255,255,255,0.12)] hover:border-[#FF6D00]/40 hover:bg-[#231E3A] transition-all group backdrop-blur-xl"
                >
                  <div className="h-10 w-10 rounded-xl bg-[#FF6D00]/15 border border-[#FF6D00]/30 flex items-center justify-center text-[#FF6D00] mb-4 group-hover:scale-110 transition-transform">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-base font-bold text-white mb-2">{item.title}</h3>
                  <p className="text-xs text-[rgba(255,255,255,0.65)] leading-relaxed font-medium">{item.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Four Feature Sections ────────────────────────────────────────── */}
      <section id="features" className="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-24 relative z-10">
        {/* Feature 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-4 text-left">
            <span className="text-xs font-bold uppercase tracking-widest text-[#FF6D00]">Feature 01</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white leading-tight">
              From Natural Language to Workflow
            </h2>
            <p className="text-sm sm:text-base text-[rgba(255,255,255,0.70)] leading-relaxed">
              Describe what you want to accomplish and turn the requirement into a structured, executable multi-agent workflow DAG.
            </p>
            <div className="pt-2">
              <Link to="/signup" className="inline-flex items-center gap-2 text-xs font-bold text-[#FF6D00] hover:text-[#FF802C]">
                Try Natural Language Generator <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
          <div className="p-6 rounded-2xl bg-[#1B1728]/80 border border-[rgba(255,255,255,0.12)] space-y-4 backdrop-blur-xl">
            <div className="flex items-center gap-3 p-3.5 rounded-xl bg-[#0E0918] border border-[rgba(255,255,255,0.12)]">
              <Bot className="h-5 w-5 text-[#FF6D00] shrink-0" />
              <span className="text-xs text-white font-mono">Prompt: "Summarize unread support emails and post alerts to Slack"</span>
            </div>
            <div className="flex justify-center text-[rgba(255,255,255,0.30)]">↓</div>
            <div className="p-3.5 rounded-xl bg-[#13102A] border border-[#FF6D00]/30 text-xs text-[#FF9E43] font-semibold flex items-center justify-between">
              <span>AI Planner Engine V4</span>
              <span className="text-[10px] bg-[#FF6D00]/20 px-2 py-0.5 rounded-full text-white">Compiled DAG</span>
            </div>
          </div>
        </div>

        {/* Feature 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center lg:flex-row-reverse">
          <div className="p-6 rounded-2xl bg-[#1B1728]/80 border border-[rgba(255,255,255,0.12)] backdrop-blur-xl">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-[rgba(255,255,255,0.08)]">
              <span className="text-xs font-bold text-white flex items-center gap-2">
                <Workflow className="h-4 w-4 text-[#FF6D00]" /> Visual Canvas
              </span>
              <span className="text-[10px] font-mono text-[rgba(255,255,255,0.45)]">4 Nodes Connected</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-left">
              <div className="p-3 rounded-xl bg-[#13102A] border border-[rgba(255,255,255,0.10)]">
                <span className="text-[10px] font-bold text-red-400 block">01 Gmail</span>
                <span className="text-xs font-semibold text-white">Search Messages</span>
              </div>
              <div className="p-3 rounded-xl bg-[#13102A] border border-[rgba(255,255,255,0.10)]">
                <span className="text-[10px] font-bold text-purple-400 block">02 AI Agent</span>
                <span className="text-xs font-semibold text-white">Extract Insights</span>
              </div>
              <div className="p-3 rounded-xl bg-[#13102A] border border-[rgba(255,255,255,0.10)]">
                <span className="text-[10px] font-bold text-amber-400 block">03 Condition</span>
                <span className="text-xs font-semibold text-white">Priority Check</span>
              </div>
              <div className="p-3 rounded-xl bg-[#13102A] border border-[rgba(255,255,255,0.10)]">
                <span className="text-[10px] font-bold text-emerald-400 block">04 Slack</span>
                <span className="text-xs font-semibold text-white">Post Notification</span>
              </div>
            </div>
          </div>
          <div className="space-y-4 text-left">
            <span className="text-xs font-bold uppercase tracking-widest text-[#FF6D00]">Feature 02</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white leading-tight">
              Design Workflows Visually
            </h2>
            <p className="text-sm sm:text-base text-[rgba(255,255,255,0.70)] leading-relaxed">
              Build and refine workflows using a visual DAG-based workflow builder with real-time node inspection and variable binding.
            </p>
          </div>
        </div>

        {/* Feature 3 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-4 text-left">
            <span className="text-xs font-bold uppercase tracking-widest text-[#FF6D00]">Feature 03</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white leading-tight">
              Connect Your APIs
            </h2>
            <p className="text-sm sm:text-base text-[rgba(255,255,255,0.70)] leading-relaxed">
              Bring together connected services and REST APIs inside one unified workflow platform.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {connectorTools.slice(0, 6).map((tool, i) => {
              const Icon = tool.icon;
              return (
                <div key={i} className="p-4 rounded-xl bg-[#1B1728] border border-[rgba(255,255,255,0.12)] text-left hover:border-[#FF6D00]/40 transition-all">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 border ${tool.color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <span className="text-xs font-bold text-white block">{tool.name}</span>
                  <span className="text-[10px] text-[rgba(255,255,255,0.45)]">{tool.category}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Feature 4 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center lg:flex-row-reverse">
          <div className="space-y-3">
            {executionControls.map((ctrl, i) => {
              const Icon = ctrl.icon;
              return (
                <div key={i} className="p-3.5 rounded-xl bg-[#1B1728] border border-[rgba(255,255,255,0.12)] flex items-center gap-3 text-left hover:bg-[#231E3A] transition-all">
                  <div className="p-2 rounded-lg bg-[#FF6D00]/15 text-[#FF6D00] shrink-0">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white">{ctrl.title}</h4>
                    <p className="text-[11px] text-[rgba(255,255,255,0.50)]">{ctrl.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="space-y-4 text-left">
            <span className="text-xs font-bold uppercase tracking-widest text-[#FF6D00]">Feature 04</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white leading-tight">
              Execute With Control
            </h2>
            <p className="text-sm sm:text-base text-[rgba(255,255,255,0.70)] leading-relaxed">
              Full visibility and governance over your automated executions with live telemetry, retry mechanics, and human approval gates.
            </p>
          </div>
        </div>
      </section>

      {/* ── AI Workflow Demonstration ──────────────────────────────────── */}
      <section id="demo" className="py-20 bg-[#13102A]/60 border-y border-[rgba(255,255,255,0.08)] relative z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <span className="text-xs font-bold uppercase tracking-widest text-[#FF6D00] block mb-2">Live Demonstration</span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-8">
            Your workflow starts with a sentence.
          </h2>

          <div className="bg-[#1B1728] border border-[rgba(255,255,255,0.12)] rounded-2xl p-6 sm:p-8 backdrop-blur-2xl shadow-2xl">
            <div className="p-4 rounded-xl bg-[#0E0918] border border-[rgba(255,255,255,0.12)] text-left flex items-center gap-3 mb-8">
              <Bot className="h-5 w-5 text-[#FF6D00] shrink-0" />
              <p className="text-sm font-semibold text-white font-mono">
                "Find my latest emails from LinkedIn, summarize them, and notify Slack."
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-[#13102A] border border-red-500/30 text-left">
                <span className="text-[10px] font-bold text-red-400 block mb-1">Step 01</span>
                <h4 className="text-xs font-bold text-white mb-1">Gmail Search</h4>
                <p className="text-[10px] text-[rgba(255,255,255,0.45)]">Query inbox for LinkedIn notifications</p>
              </div>

              <div className="p-4 rounded-xl bg-[#13102A] border border-blue-500/30 text-left">
                <span className="text-[10px] font-bold text-blue-400 block mb-1">Step 02</span>
                <h4 className="text-xs font-bold text-white mb-1">Gmail Get</h4>
                <p className="text-[10px] text-[rgba(255,255,255,0.45)]">Retrieve message details & payload</p>
              </div>

              <div className="p-4 rounded-xl bg-[#13102A] border border-purple-500/30 text-left">
                <span className="text-[10px] font-bold text-purple-400 block mb-1">Step 03</span>
                <h4 className="text-xs font-bold text-white mb-1">AI Summarize</h4>
                <p className="text-[10px] text-[rgba(255,255,255,0.45)]">Extract key summary highlights</p>
              </div>

              <div className="p-4 rounded-xl bg-[#13102A] border border-emerald-500/30 text-left">
                <span className="text-[10px] font-bold text-emerald-400 block mb-1">Step 04</span>
                <h4 className="text-xs font-bold text-white mb-1">Slack Notify</h4>
                <p className="text-[10px] text-[rgba(255,255,255,0.45)]">Dispatch alert to target channel</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Developer Tools Section ────────────────────────────────────── */}
      <section id="developers" className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        <span className="text-xs font-bold uppercase tracking-widest text-[#FF6D00] block mb-2">Integrations</span>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-12">
          Connect the tools you already use.
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {connectorTools.map((tool, idx) => {
            const Icon = tool.icon;
            return (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-[#1B1728]/80 border border-[rgba(255,255,255,0.12)] hover:border-[#FF6D00]/50 hover:bg-[#231E3A] transition-all flex flex-col items-center justify-center gap-3 backdrop-blur-xl group"
              >
                <div className={`p-3 rounded-xl border ${tool.color} group-hover:scale-110 transition-transform`}>
                  <Icon className="h-6 w-6" />
                </div>
                <span className="text-xs font-bold text-white">{tool.name}</span>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Final CTA Section ─────────────────────────────────────────── */}
      <section className="py-24 relative z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="p-10 sm:p-14 rounded-3xl bg-gradient-to-b from-[#1B1728] to-[#13102A] border border-[rgba(255,255,255,0.15)] relative overflow-hidden shadow-2xl">
            <div
              className="absolute rounded-full"
              style={{
                width: 400,
                height: 400,
                top: '-50%',
                left: '30%',
                background: 'radial-gradient(circle, rgba(255, 109, 0, 0.25) 0%, transparent 70%)',
                filter: 'blur(80px)'
              }}
            />
            <h2 className="text-3xl sm:text-5xl font-extrabold text-white mb-4 relative z-10">
              Build your first intelligent workflow.
            </h2>
            <p className="text-sm sm:text-base text-[rgba(255,255,255,0.70)] max-w-xl mx-auto mb-8 relative z-10 font-medium">
              Turn an idea into an executable workflow.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 relative z-10">
              <Link
                to="/signup"
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white font-bold text-base shadow-[0_4px_24px_rgba(255,109,0,0.40)] hover:brightness-110 active:scale-[0.96] transition-all"
              >
                Start Building
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-[#1B1728] border border-[rgba(255,255,255,0.12)] text-white font-semibold text-base hover:bg-[#231E3A] transition-all"
              >
                Log In
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <footer className="border-t border-[rgba(255,255,255,0.12)] bg-[#0A0612] py-16 relative z-10 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Brand Col */}
          <div className="col-span-2 space-y-3 text-left">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] flex items-center justify-center text-white font-bold shadow-md">
                <Zap className="h-4 w-4 fill-current" />
              </div>
              <span className="font-bold text-sm tracking-tight text-white">AgentFlow AI</span>
            </div>
            <span className="text-[10px] uppercase font-bold text-[#FF6D00] tracking-widest block">ENTERPRISE PLATFORM</span>
            <p className="text-[11px] text-[rgba(255,255,255,0.45)] leading-relaxed max-w-sm">
              Enterprise multi-agent workflow orchestration platform. Automate complex processes from natural language.
            </p>
          </div>

          {/* Links Cols */}
          <div className="space-y-3 text-left">
            <h4 className="font-bold text-white text-xs">Product</h4>
            <ul className="space-y-2 text-[rgba(255,255,255,0.50)]">
              <li><a href="#product" className="hover:text-white transition-colors">AI Generator</a></li>
              <li><a href="#features" className="hover:text-white transition-colors">Visual Canvas</a></li>
              <li><a href="#capabilities" className="hover:text-white transition-colors">API Discovery</a></li>
            </ul>
          </div>

          <div className="space-y-3 text-left">
            <h4 className="font-bold text-white text-xs">Platform</h4>
            <ul className="space-y-2 text-[rgba(255,255,255,0.50)]">
              <li><Link to="/dashboard" className="hover:text-white transition-colors">Dashboard</Link></li>
              <li><Link to="/workflows" className="hover:text-white transition-colors">Workflows</Link></li>
              <li><Link to="/analytics" className="hover:text-white transition-colors">Analytics</Link></li>
            </ul>
          </div>

          <div className="space-y-3 text-left">
            <h4 className="font-bold text-white text-xs">Resources</h4>
            <ul className="space-y-2 text-[rgba(255,255,255,0.50)]">
              <li><a href="#developers" className="hover:text-white transition-colors">Connectors</a></li>
              <li><a href="#capabilities" className="hover:text-white transition-colors">Documentation</a></li>
              <li><Link to="/login" className="hover:text-white transition-colors">Sign In</Link></li>
            </ul>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 border-t border-[rgba(255,255,255,0.08)] flex flex-col sm:flex-row items-center justify-between text-[11px] text-[rgba(255,255,255,0.40)] gap-4">
          <span>&copy; {new Date().getFullYear()} AgentFlow AI Platform. All rights reserved.</span>
          <span>Enterprise Multi-Agent Orchestration System</span>
        </div>
      </footer>
    </div>
  );
};
