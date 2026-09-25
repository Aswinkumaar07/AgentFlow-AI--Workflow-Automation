import React, { memo, useState, useRef, useCallback } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import {
  Zap,
  CheckCircle2,
  Globe,
  Cpu,
  GitBranch,
  Repeat,
  ShieldCheck,
  Mail,
  MessageSquare,
  HardDrive,
  CreditCard,
  Sparkles,
  Database,
  Clock,
  Webhook,
  Code2,
  Merge,
  Timer,
  BrainCircuit,
} from 'lucide-react';
import { useWorkflowStore } from '../../store/useWorkflowStore';

interface CustomNodeData extends Record<string, unknown> {
  label: string;
  provider: string;
  operation_id: string;
  parameters: Record<string, any>;
  step_id: string;
}

const providerIconMap: Record<string, { icon: React.ElementType; color: string }> = {
  Gmail:            { icon: Mail,          color: 'text-red-400' },
  Slack:            { icon: MessageSquare, color: 'text-green-400' },
  'Google Drive':   { icon: HardDrive,     color: 'text-blue-400' },
  GitHub:           { icon: Cpu,           color: 'text-purple-400' },
  Stripe:           { icon: CreditCard,    color: 'text-indigo-400' },
  OpenAI:           { icon: Sparkles,      color: 'text-amber-400' },
  Notion:           { icon: Database,      color: 'text-gray-400' },
  'Generic REST':   { icon: Globe,         color: 'text-cyan-400' },
  Condition:        { icon: GitBranch,     color: 'text-amber-500' },
  IF:               { icon: GitBranch,     color: 'text-amber-500' },
  Switch:           { icon: GitBranch,     color: 'text-orange-400' },
  Loop:             { icon: Repeat,        color: 'text-blue-400' },
  Merge:            { icon: Merge,         color: 'text-teal-400' },
  Approval:         { icon: ShieldCheck,   color: 'text-purple-500' },
  'Human Approval': { icon: ShieldCheck,   color: 'text-purple-500' },
  human_approval:   { icon: ShieldCheck,   color: 'text-purple-500' },
  Delay:            { icon: Timer,         color: 'text-rose-400' },
  AI:               { icon: BrainCircuit,  color: 'text-violet-400' },
  Code:             { icon: Code2,         color: 'text-emerald-400' },
  Webhook:          { icon: Webhook,       color: 'text-pink-400' },
  Schedule:         { icon: Clock,         color: 'text-sky-400' },
  Trigger:          { icon: Zap,           color: 'text-yellow-400' },
};

const OAUTH_REQUIRED_PROVIDERS = ['gmail', 'slack', 'google drive', 'drive', 'google sheets', 'sheets', 'github', 'stripe', 'openai', 'notion'];

const getProviderMeta = (provider: string) => {
  const norm = String(provider || '').trim().toLowerCase();
  for (const [key, val] of Object.entries(providerIconMap)) {
    if (key.toLowerCase() === norm) {
      return val;
    }
  }
  return providerIconMap[provider] ?? { icon: Globe, color: 'text-muted-foreground' };
};

export const CustomNode: React.FC<NodeProps> = memo(({ data, selected, id }) => {
  const nodeData = data as unknown as CustomNodeData;
  const { updateNodeData } = useWorkflowStore();

  const isCondition = nodeData.provider === 'Condition' || nodeData.provider === 'IF' || nodeData.provider === 'Switch';

  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(nodeData.label || nodeData.provider);
  const inputRef = useRef<HTMLInputElement>(null);

  const { icon: Icon, color: iconColor } = getProviderMeta(nodeData.provider);

  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setRenameValue(nodeData.label || nodeData.provider);
    setIsRenaming(true);
    setTimeout(() => inputRef.current?.select(), 50);
  }, [nodeData.label, nodeData.provider]);

  const commitRename = useCallback(() => {
    if (renameValue.trim()) {
      updateNodeData(id, { label: renameValue.trim() });
    }
    setIsRenaming(false);
  }, [renameValue, id, updateNodeData]);

  const handleRenameKey = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') commitRename();
    if (e.key === 'Escape') setIsRenaming(false);
    e.stopPropagation();
  }, [commitRename]);

  const params = nodeData.parameters || {};
  const authLabel = String(params.auth_account_label || '');
  const authStatus = String(params.auth_status || '');
  const credentialId = params.credential_id;

  const isConnected = authStatus === 'active' && !!authLabel && !!credentialId;

  const normProvider = String(nodeData.provider || '').trim().toLowerCase();
  const requiresOAuth = OAUTH_REQUIRED_PROVIDERS.includes(normProvider) || OAUTH_REQUIRED_PROVIDERS.some((p) => normProvider.includes(p));

  if (isConnected) {
    console.log(`[AUTH-6] Canvas rendered connected node: provider=${nodeData.provider} label=${nodeData.label} account=${authLabel}`);
  }

  return (
    <div
      className={`w-64 rounded-2xl border backdrop-blur-xl p-4 shadow-xl transition-all duration-200 ${
        selected
          ? 'bg-[#1B1728] border-[#FF6D00] ring-2 ring-[#FF6D00]/40 shadow-[0_0_25px_rgba(255,109,0,0.30)]'
          : 'bg-[#13102A]/90 border-[rgba(255,255,255,0.12)] hover:border-[#FF6D00]/40 hover:shadow-[0_0_15px_rgba(255,109,0,0.15)]'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-[#FF6D00] !w-3.5 !h-3.5 !-top-2 !border-2 !border-[#0E0918] shadow-[0_0_8px_rgba(255,109,0,0.5)]" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.10)] pb-2.5 mb-2.5">
        <div className="flex items-center gap-2">
          <div className={`h-8 w-8 rounded-xl bg-[#FF6D00]/10 border border-[#FF6D00]/25 flex items-center justify-center shrink-0 ${iconColor}`}>
            <Icon className="h-4 w-4" />
          </div>
          <div className="flex flex-col min-w-0">
            {isRenaming ? (
              <input
                ref={inputRef}
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onBlur={commitRename}
                onKeyDown={handleRenameKey}
                className="text-xs font-semibold bg-[#0E0918] text-white border border-[#FF6D00] rounded-lg px-1.5 py-0.5 w-28 outline-none"
                autoFocus
              />
            ) : (
              <span
                className="font-bold text-xs text-white truncate max-w-[130px] cursor-text hover:text-[#FF6D00] transition"
                onDoubleClick={handleDoubleClick}
                title="Double-click to rename"
              >
                {nodeData.label || nodeData.provider}
              </span>
            )}
            <span className="text-[9px] text-[#A098AE] truncate max-w-[130px]">{nodeData.provider}</span>
          </div>
        </div>
        <span className="px-2 py-0.5 rounded-full text-[9px] font-mono bg-[#1B1728] text-[#FF6D00] border border-[rgba(255,255,255,0.08)] uppercase shrink-0 font-bold">
          {nodeData.step_id?.slice(-5)}
        </span>
      </div>

      {/* Operation Details */}
      <div className="space-y-1.5">
        <p className="text-[11px] font-mono text-[#A098AE] truncate">{nodeData.operation_id}</p>
        {Object.keys(nodeData.parameters || {}).length > 0 && (
          <div className="p-2 rounded-xl bg-[#0E0918]/80 border border-[rgba(255,255,255,0.08)] text-[10px] font-mono space-y-0.5 max-h-16 overflow-hidden">
            {Object.entries(nodeData.parameters || {})
              .filter(([k]) => !k.startsWith('auth_'))
              .slice(0, 3)
              .map(([k, v]) => (
                <div key={k} className="flex justify-between gap-1">
                  <span className="text-[#7A748E] shrink-0">{k}:</span>
                  <span className="truncate font-semibold text-white">{String(v)}</span>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* Sprint AUTH-3: Pure Parameter-Driven Connected Badge */}
      {isConnected ? (
        <div className="mt-2.5 p-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-medium flex items-center justify-between">
          <span className="flex items-center gap-1.5 truncate font-semibold">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
            <span className="truncate text-white">{authLabel || 'Connected'}</span>
          </span>
          <span className="text-[9px] font-mono bg-emerald-500/20 px-1.5 py-0.5 rounded-md shrink-0 font-bold text-emerald-400">Connected</span>
        </div>
      ) : (
        requiresOAuth && (
          <div className="mt-2.5 p-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[10px] font-medium flex items-center justify-between">
            <span className="flex items-center gap-1.5 font-semibold">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0 animate-pulse shadow-[0_0_6px_rgba(251,191,36,0.8)]" />
              <span className="text-amber-300">Unbound Account</span>
            </span>
            <span className="text-[9px] font-mono bg-amber-500/20 px-1.5 py-0.5 rounded-md shrink-0 font-bold text-amber-400">Needs OAuth</span>
          </div>
        )
      )}

      {/* Status Footer */}
      <div className="mt-3 pt-2 border-t border-[rgba(255,255,255,0.08)] flex items-center justify-between text-[10px] text-[#A098AE]">
        <span className="flex items-center gap-1 text-emerald-400 font-semibold">
          <CheckCircle2 className="h-3 w-3 text-emerald-400" /> Ready
        </span>
        <span className="font-mono text-[#7A748E]">~50ms</span>
      </div>

      {/* Handles */}
      {isCondition ? (
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="true_branch"
            style={{ left: '30%' }}
            className="!bg-emerald-500 !w-3.5 !h-3.5 !-bottom-2 !border-2 !border-[#0E0918] shadow-[0_0_8px_rgba(16,185,129,0.5)]"
            title="TRUE Branch"
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="false_branch"
            style={{ left: '70%' }}
            className="!bg-rose-500 !w-3.5 !h-3.5 !-bottom-2 !border-2 !border-[#0E0918] shadow-[0_0_8px_rgba(244,63,94,0.5)]"
            title="FALSE Branch"
          />
        </>
      ) : (
        <Handle type="source" position={Position.Bottom} className="!bg-[#FF6D00] !w-3.5 !h-3.5 !-bottom-2 !border-2 !border-[#0E0918] shadow-[0_0_8px_rgba(255,109,0,0.5)]" />
      )}
    </div>
  );
});

CustomNode.displayName = 'CustomNode';
