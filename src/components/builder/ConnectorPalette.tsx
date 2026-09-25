import React, { useState } from 'react';
import {
  Search,
  Mail,
  HardDrive,
  MessageSquare,
  GitBranch,
  CreditCard,
  Sparkles,
  Globe,
  Database,
  Zap,
  Clock,
  Webhook,
  Code2,
  Repeat,
  Merge,
  ShieldCheck,
  Timer,
  BrainCircuit,
  ChevronDown,
} from 'lucide-react';

interface ConnectorItem {
  id: string;
  name: string;
  category: 'Triggers' | 'Flow Control' | 'Actions' | 'Connectors';
  operation_id: string;
  icon: React.ElementType;
  color: string;
  defaultParams: Record<string, any>;
  description: string;
}

const connectors: ConnectorItem[] = [
  // ── Triggers ──────────────────────────────────────────────
  {
    id: 'manual-trigger',
    name: 'Manual Trigger',
    category: 'Triggers',
    operation_id: 'trigger.manual',
    icon: Zap,
    color: 'text-yellow-400',
    defaultParams: {},
    description: 'Run workflow manually on demand',
  },
  {
    id: 'webhook-trigger',
    name: 'Webhook',
    category: 'Triggers',
    operation_id: 'trigger.webhook',
    icon: Webhook,
    color: 'text-pink-400',
    defaultParams: { path: '/webhook/my-hook', method: 'POST' },
    description: 'Receive HTTP webhook events',
  },
  {
    id: 'schedule-trigger',
    name: 'Schedule',
    category: 'Triggers',
    operation_id: 'trigger.schedule',
    icon: Clock,
    color: 'text-sky-400',
    defaultParams: { cron: '0 9 * * 1-5' },
    description: 'Run on a cron schedule',
  },

  // ── Flow Control ───────────────────────────────────────────
  {
    id: 'condition',
    name: 'Condition',
    category: 'Flow Control',
    operation_id: 'flow.condition',
    icon: GitBranch,
    color: 'text-amber-400',
    defaultParams: { left_value: '{{$node.Step1.output}}', operator: 'Contains', right_value: 'Invoice' },
    description: 'IF / ELSE branching logic',
  },
  {
    id: 'switch',
    name: 'Switch',
    category: 'Flow Control',
    operation_id: 'flow.switch',
    icon: GitBranch,
    color: 'text-orange-400',
    defaultParams: { field: '{{$node.Step1.status}}' },
    description: 'Multi-branch switch/case',
  },
  {
    id: 'loop',
    name: 'Loop',
    category: 'Flow Control',
    operation_id: 'flow.loop',
    icon: Repeat,
    color: 'text-blue-400',
    defaultParams: { items: '{{$node.Step1.results}}', batch_size: 10 },
    description: 'Iterate over a list of items',
  },
  {
    id: 'merge',
    name: 'Merge',
    category: 'Flow Control',
    operation_id: 'flow.merge',
    icon: Merge,
    color: 'text-teal-400',
    defaultParams: { mode: 'wait_all' },
    description: 'Join parallel branches',
  },
  {
    id: 'approval',
    name: 'Approval',
    category: 'Flow Control',
    operation_id: 'flow.approval',
    icon: ShieldCheck,
    color: 'text-purple-400',
    defaultParams: { approvers: 'admin@company.com', timeout_hours: 24 },
    description: 'Human approval gate',
  },
  {
    id: 'delay',
    name: 'Delay',
    category: 'Flow Control',
    operation_id: 'flow.delay',
    icon: Timer,
    color: 'text-rose-400',
    defaultParams: { duration_seconds: 60 },
    description: 'Wait for a fixed duration',
  },

  // ── Actions ────────────────────────────────────────────────
  {
    id: 'ai-node',
    name: 'AI',
    category: 'Actions',
    operation_id: 'ai.llm.completion',
    icon: BrainCircuit,
    color: 'text-violet-400',
    defaultParams: { model: 'gpt-4o', prompt: 'Summarize this: {{$node.Step1.text}}' },
    description: 'Call an AI language model',
  },
  {
    id: 'code-node',
    name: 'Code',
    category: 'Actions',
    operation_id: 'code.execute',
    icon: Code2,
    color: 'text-emerald-400',
    defaultParams: { language: 'javascript', code: 'return { result: items.length };' },
    description: 'Run custom JavaScript/Python',
  },
  {
    id: 'generic-rest',
    name: 'REST API',
    category: 'Actions',
    operation_id: 'generic.http.request',
    icon: Globe,
    color: 'text-cyan-400',
    defaultParams: { method: 'GET', url: 'https://api.example.com/data' },
    description: 'Generic HTTP request',
  },

  // ── Connectors ─────────────────────────────────────────────
  {
    id: 'gmail',
    name: 'Gmail',
    category: 'Connectors',
    operation_id: 'gmail.messages.list',
    icon: Mail,
    color: 'text-red-400',
    defaultParams: { query: 'label:invoices is:unread' },
    description: 'Read or send Gmail emails',
  },
  {
    id: 'slack',
    name: 'Slack',
    category: 'Connectors',
    operation_id: 'slack.chat.postMessage',
    icon: MessageSquare,
    color: 'text-green-400',
    defaultParams: { channel: '#general', text: '{{$node.Step1.summary}}' },
    description: 'Post messages to Slack',
  },
  {
    id: 'drive',
    name: 'Google Drive',
    category: 'Connectors',
    operation_id: 'drive.files.create',
    icon: HardDrive,
    color: 'text-blue-400',
    defaultParams: { folder: 'Documents', filename: 'report.pdf' },
    description: 'Upload or manage Drive files',
  },
  {
    id: 'github',
    name: 'GitHub',
    category: 'Connectors',
    operation_id: 'github.issues.create',
    icon: GitBranch,
    color: 'text-purple-400',
    defaultParams: { repo: 'owner/repo', title: 'New Issue' },
    description: 'Manage GitHub issues & PRs',
  },
  {
    id: 'stripe',
    name: 'Stripe',
    category: 'Connectors',
    operation_id: 'stripe.charges.create',
    icon: CreditCard,
    color: 'text-indigo-400',
    defaultParams: { amount: 1000, currency: 'usd' },
    description: 'Charge customers via Stripe',
  },
  {
    id: 'openai',
    name: 'OpenAI',
    category: 'Connectors',
    operation_id: 'openai.chat.completions',
    icon: Sparkles,
    color: 'text-amber-400',
    defaultParams: { model: 'gpt-4o', max_tokens: 1024 },
    description: 'OpenAI Chat Completions',
  },
  {
    id: 'notion',
    name: 'Notion',
    category: 'Connectors',
    operation_id: 'notion.pages.create',
    icon: Database,
    color: 'text-gray-400',
    defaultParams: { database: 'Roadmap', title: 'New Page' },
    description: 'Create/update Notion pages',
  },
];

const CATEGORIES = ['All', 'Triggers', 'Flow Control', 'Actions', 'Connectors'] as const;
type Category = typeof CATEGORIES[number];

export const ConnectorPalette: React.FC = () => {
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<Category>('All');
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const filtered = connectors.filter((c) => {
    const matchesCategory = selectedCategory === 'All' || c.category === selectedCategory;
    const matchesSearch =
      c.name.toLowerCase().includes(query.toLowerCase()) ||
      c.operation_id.toLowerCase().includes(query.toLowerCase()) ||
      c.description.toLowerCase().includes(query.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const grouped = CATEGORIES.slice(1).reduce<Record<string, ConnectorItem[]>>((acc, cat) => {
    const items = filtered.filter((c) => c.category === cat);
    if (items.length > 0) acc[cat] = items;
    return acc;
  }, {});

  const onDragStart = (e: React.DragEvent, item: ConnectorItem) => {
    e.dataTransfer.setData('application/reactflow', JSON.stringify(item));
    e.dataTransfer.effectAllowed = 'move';
  };

  const toggleCollapse = (cat: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  return (
    <aside className="w-64 border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-2xl flex flex-col h-full rounded-2xl shadow-xl overflow-hidden">
      {/* Search & Filter Header */}
      <div className="p-3 border-b border-[rgba(255,255,255,0.10)] space-y-2.5 bg-[#1B1728]/40">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[#A098AE]">Node Palette</h3>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#A098AE]" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search nodes..."
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#0E0918] text-white placeholder-[#7A748E] rounded-xl border border-[rgba(255,255,255,0.12)] focus:outline-none focus:border-[#FF6D00] focus:ring-1 focus:ring-[#FF6D00] transition"
          />
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap gap-1">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold whitespace-nowrap transition-all duration-150 ${
                selectedCategory === cat
                  ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-[0_0_10px_rgba(255,109,0,0.30)]'
                  : 'bg-[#1B1728] text-[#A098AE] hover:text-white hover:bg-[#231E3A]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Node Groups */}
      <div className="flex-1 overflow-y-auto p-1.5 space-y-2 scrollbar-thin scrollbar-thumb-[#231E3A]">
        {Object.entries(grouped).map(([cat, items]) => (
          <div key={cat}>
            {/* Category Header */}
            <button
              onClick={() => toggleCollapse(cat)}
              className="w-full flex items-center justify-between px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-[#A098AE] hover:text-white hover:bg-[#1B1728]/50 rounded-lg transition"
            >
              <span>{cat}</span>
              <span className="flex items-center gap-1">
                <span className="bg-[#1B1728] border border-[rgba(255,255,255,0.10)] rounded px-1.5 text-[9px] text-white font-mono">{items.length}</span>
                <ChevronDown
                  className={`h-3 w-3 transition-transform ${collapsed.has(cat) ? '-rotate-90' : ''}`}
                />
              </span>
            </button>

            {/* Items */}
            {!collapsed.has(cat) && (
              <div className="px-1 pt-1 pb-1 space-y-1">
                {items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <div
                      key={item.id}
                      draggable
                      onDragStart={(e) => onDragStart(e, item)}
                      className="p-2.5 rounded-xl border border-[rgba(255,255,255,0.08)] bg-[#1B1728]/60 hover:bg-[#231E3A] hover:border-[#FF6D00]/50 hover:shadow-[0_0_15px_rgba(255,109,0,0.15)] cursor-grab active:cursor-grabbing transition group flex items-center gap-2.5"
                    >
                      <div className={`h-7 w-7 rounded-lg bg-[#FF6D00]/10 border border-[#FF6D00]/20 flex items-center justify-center shrink-0 ${item.color}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-white group-hover:text-[#FF6D00] transition truncate">{item.name}</p>
                        <p className="text-[10px] text-[#A098AE] truncate">{item.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="p-6 text-center text-xs text-[#A098AE]">
            No nodes match <span className="font-mono text-[#FF6D00]">"{query}"</span>
          </div>
        )}
      </div>

      {/* Footer hint */}
      <div className="p-2.5 border-t border-[rgba(255,255,255,0.10)] text-[10px] text-[#A098AE] text-center font-mono bg-[#1B1728]/40">
        Drag any node onto the canvas
      </div>
    </aside>
  );
};
