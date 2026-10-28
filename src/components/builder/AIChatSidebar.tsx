import React, { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import { useOAuthStore } from '../../store/useOAuthStore';
import { aiApi } from '../../api/ai';
import { OAuthConnectModal } from '../oauth/OAuthConnectModal';
import { isInternalProvider, isGoogleService } from '../../utils/oauthReadiness';
import { Sparkles, Send, Loader2, History, Lightbulb, AlertCircle, ShieldCheck, CheckCircle2, Clock } from 'lucide-react';

interface NeedsAuthItem {
  step_id: string;
  provider: string;
  oauth_connect_url: string;
}

interface AIChatSidebarProps {
  onOpenSchedules?: () => void;
}

export const AIChatSidebar: React.FC<AIChatSidebarProps> = ({ onOpenSchedules }) => {
  const [, setSearchParams] = useSearchParams();
  const [prompt, setPrompt] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [createdSchedule, setCreatedSchedule] = useState<any>(null);
  const [connectModalProvider, setConnectModalProvider] = useState<NeedsAuthItem | null>(null);

  const { setWorkflow, isGenerating, setIsGenerating, historyPrompts, addPromptHistory } =
    useWorkflowStore();
  const nodes = useWorkflowStore((state) => state.nodes);
  const connections = useOAuthStore((state) => state.connections);

  // Dynamically derive Invisible OAuth panel status from reactive nodes and connections
  const displayOauthStatus = useMemo(() => {
    if (!nodes || nodes.length === 0) return null;

    const steps = nodes.map((n) => {
      const data = n.data || {};
      const provider = (data as any).provider || (n as any).provider || 'Generic';
      const parameters = (data as any).parameters || (n as any).parameters || {};
      return {
        id: n.id,
        step_id: n.id,
        provider,
        parameters,
      };
    });

    const activeConnections = Array.isArray(connections)
      ? connections.filter((c) => c && (c.status === 'CONNECTED' || (c as any).is_connected === true))
      : [];

    const isNodeBound = (nodeParams: any, provider: string): boolean => {
      if (nodeParams?.auth_account_label || nodeParams?.credential_id || nodeParams?.auth_status === 'active') {
        return true;
      }
      if (!provider) return false;
      const normNode = provider.trim().toLowerCase();
      return activeConnections.some((c) => {
        if (!c || !c.provider) return false;
        const normConn = c.provider.trim().toLowerCase();
        if (normNode === normConn) return true;
        if (isGoogleService(normNode) && isGoogleService(normConn)) return true;
        return normNode.includes(normConn) || normConn.includes(normNode);
      });
    };

    const oauthSteps = steps.filter((s) => !isInternalProvider(s.provider));

    if (oauthSteps.length > 0) {
      const boundCount = oauthSteps.filter((s) => isNodeBound(s.parameters, s.provider)).length;
      const unboundSteps = oauthSteps.filter((s) => !isNodeBound(s.parameters, s.provider));

      const seenProviders = new Set<string>();
      const needsAuth: NeedsAuthItem[] = [];
      for (const s of unboundSteps) {
        const norm = s.provider.trim().toLowerCase();
        if (!seenProviders.has(norm)) {
          seenProviders.add(norm);
          needsAuth.push({
            step_id: s.id,
            provider: s.provider,
            oauth_connect_url: '',
          });
        }
      }

      return {
        bound: boundCount,
        total: oauthSteps.length,
        needsAuth,
      };
    } else if (steps.length > 0) {
      return {
        bound: steps.length,
        total: steps.length,
        needsAuth: [],
      };
    }

    return null;
  }, [nodes, connections]);

  React.useEffect(() => {
    console.log('[AI30-REFRESH] AIChatSidebar mounted');
    return () => console.log('[AI30-REFRESH] AIChatSidebar UNMOUNTED');
  }, []);

  const handleGenerate = async (targetPrompt?: string) => {
    const finalPrompt = targetPrompt || prompt;
    if (!finalPrompt.trim() || isGenerating) return;

    try {
      setErrorMsg(null);
      setIsGenerating(true);
      addPromptHistory(finalPrompt);

      const res = await aiApi.generateWorkflow(finalPrompt);
      setWorkflow(res);
      setPrompt('');

      const genWfId =
        (res as any)?.workflow_id ||
        (res as any)?.workflow_json?.workflow_id ||
        (res as any)?.data?.workflow_id ||
        (res as any)?.data?.workflow_json?.workflow_id;
      if (genWfId) {
        setSearchParams({ id: genWfId }, { replace: true });
        window.dispatchEvent(new CustomEvent('workflow-created', { detail: { workflowId: genWfId } }));
      }

      console.log('[AI30 SCHEDULE] creation processing started');
      const sched = (res as any)?.schedule || (res as any)?.data?.schedule;
      if (sched) {
        console.log('[AI30 SCHEDULE] schedule detected:', sched);
        setCreatedSchedule(sched);
        console.log('[AI30 SCHEDULE] state updated');
      } else {
        console.log('[AI30 SCHEDULE] no schedule detected');
        setCreatedSchedule(null);
      }
      console.log('[AI30 SCHEDULE] creation processing completed');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate workflow. Check backend connection.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <aside className="w-80 border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-2xl flex flex-col h-full rounded-2xl shadow-xl overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[rgba(255,255,255,0.10)] flex items-center gap-3 bg-[#1B1728]/40">
        <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center font-bold shadow-[0_0_10px_rgba(255,109,0,0.20)]">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <h2 className="text-sm font-bold text-white tracking-tight">AI Workflow Architect</h2>
          <p className="text-[10px] text-[#A098AE]">Natural Language → DAG + Auto OAuth Binding</p>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-5 scrollbar-thin scrollbar-thumb-[#231E3A]">
        {/* Error */}
        {errorMsg && (
          <div className="p-3 text-xs rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Schedule Confirmation Banner */}
        {createdSchedule && (
          <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 overflow-hidden p-3 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-indigo-400" />
                <span className="text-xs font-semibold text-indigo-300">Schedule Created ✓</span>
              </div>
              <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase">
                {createdSchedule.status || 'ACTIVE'}
              </span>
            </div>
            <div className="text-[11px] text-slate-300 space-y-1">
              <p className="truncate font-medium">{createdSchedule.name || createdSchedule.prompt}</p>
              {createdSchedule.version_number && (
                <p className="text-[10px] text-indigo-400 font-semibold">Pinned Version: v{createdSchedule.version_number}</p>
              )}
              {createdSchedule.next_run_at && (
                <p className="text-[10px] text-slate-400">
                  Next Run: {new Date(createdSchedule.next_run_at).toLocaleTimeString()}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (onOpenSchedules) {
                  onOpenSchedules();
                } else {
                  window.dispatchEvent(new CustomEvent('open-schedules-modal'));
                }
              }}
              className="w-full mt-1 py-1.5 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-medium flex items-center justify-center gap-1.5 transition-colors"
            >
              <Clock className="h-3.5 w-3.5" />
              View Schedule
            </button>
          </div>
        )}

        {/* OAuth Bind Result */}
        {displayOauthStatus && (
          <div className="rounded-xl border border-[rgba(255,255,255,0.10)] bg-[#1B1728]/50 overflow-hidden">
            <div className="flex items-center gap-2 px-3 py-2 bg-emerald-500/10 border-b border-[rgba(255,255,255,0.08)]">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-[11px] font-semibold text-emerald-400">Invisible OAuth</span>
            </div>
            <div className="p-3 space-y-2">
              <div className="flex items-center gap-2 text-[11px]">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                <span>
                  <span className="font-bold text-white">{displayOauthStatus.bound}</span>
                  <span className="text-[#A098AE]"> accounts auto-bound</span>
                </span>
              </div>
              {displayOauthStatus.needsAuth.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">Requires Connection</p>
                  {displayOauthStatus.needsAuth.map((item) => (
                    <button
                      type="button"
                      key={item.step_id}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setConnectModalProvider(item);
                      }}
                      className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg border border-amber-500/20 bg-amber-500/10 hover:bg-amber-500/20 text-white text-[11px] transition"
                    >
                      <span className="font-medium">{item.provider}</span>
                      <span className="text-amber-400 text-[10px]">Connect →</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Prompt Suggestions */}
        <div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-[#A098AE] uppercase tracking-wider mb-2">
            <Lightbulb className="h-3.5 w-3.5 text-[#FF6D00]" />
            <span>Prompt Suggestions</span>
          </div>
          <div className="space-y-1.5">
            {historyPrompts.slice(0, 3).map((sug, idx) => (
              <button
                key={idx}
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleGenerate(sug);
                }}
                disabled={isGenerating}
                className="w-full text-left p-2.5 rounded-xl border border-[rgba(255,255,255,0.08)] bg-[#1B1728]/60 hover:bg-[#231E3A] hover:border-[#FF6D00]/40 text-xs text-[#A098AE] hover:text-white transition-all line-clamp-2"
              >
                {sug}
              </button>
            ))}
          </div>
        </div>

        {/* Prompt History */}
        {historyPrompts.length > 3 && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[#A098AE] uppercase tracking-wider mb-2">
              <History className="h-3.5 w-3.5 text-[#A098AE]" />
              <span>Recent History</span>
            </div>
            <div className="space-y-1">
              {historyPrompts.slice(3).map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => setPrompt(item)}
                  className="text-xs text-[#A098AE] hover:text-white cursor-pointer truncate py-1 px-2 rounded-lg hover:bg-[#1B1728] transition"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Prompt Input Footer */}
      <div className="p-4 border-t border-[rgba(255,255,255,0.10)] bg-[#1B1728]/40">
        <div className="space-y-2.5">
          <div className="relative">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  e.stopPropagation();
                  handleGenerate();
                }
              }}
              placeholder="Describe your workflow... (Enter to send)"
              rows={3}
              className="w-full p-3 text-xs bg-[#0E0918] border border-[rgba(255,255,255,0.12)] text-white placeholder-[#7A748E] rounded-xl focus:outline-none focus:border-[#FF6D00] focus:ring-1 focus:ring-[#FF6D00] resize-none transition"
            />
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleGenerate();
            }}
            disabled={!prompt.trim() || isGenerating}
            className="w-full py-2.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl hover:opacity-95 transition flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(255,109,0,0.35)] disabled:opacity-50 disabled:shadow-none"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Generating + Binding OAuth…
              </>
            ) : (
              <>
                <Sparkles className="h-3.5 w-3.5" /> Generate Workflow <Send className="h-3 w-3" />
              </>
            )}
          </button>
        </div>
      </div>

      {/* OAuth Connect Modal triggered from needsAuth list */}
      {connectModalProvider && (
        <OAuthConnectModal
          isOpen={true}
          provider={connectModalProvider.provider}
          connectUrl={connectModalProvider.oauth_connect_url}
          onConnected={() => {
            useOAuthStore.getState().fetchOAuthData();
            setConnectModalProvider(null);
          }}
          onClose={() => setConnectModalProvider(null)}
        />
      )}
    </aside>
  );
};
