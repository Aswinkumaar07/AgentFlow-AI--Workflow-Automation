import React, { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { AIChatSidebar } from '../components/builder/AIChatSidebar';
import { ConnectorPalette } from '../components/builder/ConnectorPalette';
import { WorkflowCanvas } from '../components/builder/WorkflowCanvas';
import { NodeInspector } from '../components/builder/NodeInspector';
import { JSONViewerModal } from '../components/builder/JSONViewerModal';
import { VersionHistoryModal } from '../components/builder/VersionHistoryModal';
import { ExecutionHistoryModal } from '../components/builder/ExecutionHistoryModal';
import { ExecutionAnalyticsModal } from '../components/builder/ExecutionAnalyticsModal';
import { SchedulesTriggersModal } from '../components/builder/SchedulesTriggersModal';
import { ExecutionResultInspector } from '../components/builder/ExecutionResultInspector';
import { useWorkflowStore } from '../store/useWorkflowStore';
import { useExecutionStore } from '../store/useExecutionStore';
import { useOAuthStore } from '../store/useOAuthStore';
import { workflowApi } from '../api/workflows';
import { getAutoLayoutElements } from '../utils/layout';
import { isInternalProvider, checkProviderReadiness, rebindNodesWithOAuthConnections } from '../utils/oauthReadiness';
import { restoreWorkflowOAuthSnapshot } from '../utils/oauthWorkflowPersistence';
import {
  Play,
  Code2,
  Trash2,
  CheckCircle2,
  Loader2,
  LayoutGrid,
  Undo2,
  Redo2,
  History,
  Sparkles,
  Cpu,
  Copy,
  Clipboard,
  Layers,
  Workflow,
  XCircle,
  MousePointerClick,
  PlayCircle,
  Info,
  BarChart3,
  Clock,
} from 'lucide-react';

export const WorkflowBuilderPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const urlWorkflowId = searchParams.get('id');

  const {
    workflowId,
    currentVersionNumber,
    restoredNotice,
    setRestoredNotice,
    nodes,
    edges,
    setNodes,
    setEdges,
    setWorkflow,
    selectedNode,
    clipboard,
    undo,
    redo,
    historyStack,
    futureStack,
    copySelectedNodes,
    pasteNodes,
    duplicateNode,
  } = useWorkflowStore();

  const connections = useOAuthStore((state) => state.connections);

  const [activeTab, setActiveTab] = useState<'palette' | 'ai'>('palette');
  const [isJSONOpen, setIsJSONOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isExecHistoryOpen, setIsExecHistoryOpen] = useState(false);
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);
  const [isSchedulesOpen, setIsSchedulesOpen] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<{
    ok: boolean;
    message: string;
    execution_id?: string;
    nodes_executed?: number;
    total_nodes?: number;
    node_results?: any[];
    final_output?: any;
    status?: string;
    can_resume?: boolean;
    checkpoint_timestamp?: number;
  } | null>(null);

  const selectedNodeIds = nodes.filter((n) => n.selected).map((n) => n.id);

  // Synchronize restored workflow nodes with real OAuth connections once connection data resolves
  React.useEffect(() => {
    if (nodes && nodes.length > 0) {
      const rebound = rebindNodesWithOAuthConnections(nodes, connections);
      const changed = JSON.stringify(rebound) !== JSON.stringify(nodes);
      if (changed) {
        console.log(`[OAuthPersistence] Rebound ${nodes.length} nodes with active OAuth connections.`);
        setNodes(rebound);
      }
    }
  }, [connections, nodes, setNodes]);

  React.useEffect(() => {
    console.log('[AI30-REFRESH] WorkflowBuilderPage mounted, urlWorkflowId:', urlWorkflowId);

    // Hydrate workflow from backend if urlWorkflowId is present and not matching loaded store state
    if (urlWorkflowId) {
      const { workflowId: currentWfId, nodes: currentNodes, loadWorkflowFromBackend } = useWorkflowStore.getState();
      if (currentWfId !== urlWorkflowId || currentNodes.length === 0) {
        loadWorkflowFromBackend(urlWorkflowId);
      }
    }

    // Restore pending workflow DAG snapshot if coming back from OAuth redirect
    restoreWorkflowOAuthSnapshot();

    // Refresh OAuth connections data so node readiness updates and node re-binding fires
    useOAuthStore.getState().fetchOAuthData().then(() => {
      const latestNodes = useWorkflowStore.getState().nodes;
      const latestConns = useOAuthStore.getState().connections;
      if (latestNodes && latestNodes.length > 0) {
        const rebound = rebindNodesWithOAuthConnections(latestNodes, latestConns);
        if (JSON.stringify(rebound) !== JSON.stringify(latestNodes)) {
          setNodes(rebound);
        }
      }
    }).catch((err) => {
      console.error('[OAuthPersistence] Error refreshing OAuth store on mount:', err);
    });

    const handleBeforeUnload = () => {
      console.log('[AI30-REFRESH] BEFOREUNLOAD DETECTED! Page is unloading/reloading!');
    };
    const handleUnload = () => {
      console.log('[AI30-REFRESH] UNLOAD DETECTED! Page document unloaded!');
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('unload', handleUnload);
    return () => {
      console.log('[AI30-REFRESH] WorkflowBuilderPage UNMOUNTED');
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('unload', handleUnload);
    };
  }, [urlWorkflowId]);


  const handleAutoLayout = useCallback(() => {
    if (nodes.length === 0) return;
    const { nodes: ln, edges: le } = getAutoLayoutElements(nodes, edges);
    setNodes(ln);
    setEdges(le);
  }, [nodes, edges, setNodes, setEdges]);

  const handleCopy = useCallback(() => {
    const ids = selectedNodeIds.length > 0 ? selectedNodeIds : selectedNode ? [selectedNode.id] : [];
    if (ids.length > 0) copySelectedNodes(ids);
  }, [selectedNodeIds, selectedNode, copySelectedNodes]);

  const handleDuplicate = useCallback(() => {
    const ids = selectedNodeIds.length > 0 ? selectedNodeIds : selectedNode ? [selectedNode.id] : [];
    ids.forEach((id) => duplicateNode(id));
  }, [selectedNodeIds, selectedNode, duplicateNode]);

  const handleExecute = async () => {
    if (nodes.length === 0) return;
    setIsExecuting(true);
    setExecutionResult(null);
    useExecutionStore.getState().resetExecution();

    const mappedNodes = nodes.map((n) => {
      const mergedParams = {
        ...((n as any).parameters || {}),
        ...((n.data as any)?.parameters || {}),
      };
      if ((n.data as any)?.operation_id?.includes('gmail') || (n.data as any)?.provider?.toLowerCase() === 'gmail') {
        if (mergedParams.max_results === undefined || mergedParams.max_results === null) {
          mergedParams.max_results = 10;
        } else {
          let parsed = parseInt(String(mergedParams.max_results), 10);
          if (isNaN(parsed) || parsed < 1) parsed = 10;
          else if (parsed > 50) {
            console.warn(`[AI-19.3][SAFE_MAXIMUM] original=${parsed} clamped=50`);
            parsed = 50;
          }
          mergedParams.max_results = parsed;
        }
        console.log(`[AI-19.3][MAX_RESULTS_CONFIGURED] node=${n.id} max_results=${mergedParams.max_results}`);
        console.log(`[AI-20][MAX_RESULTS_PAYLOAD] node=${n.id} max_results=${mergedParams.max_results}`);
      }
      return {
        id: n.id,
        step_id: n.id,
        provider: (n.data as any).provider || 'Generic',
        operation_id: (n.data as any).operation_id || 'generic.http.request',
        parameters: mergedParams,
        dependencies: edges.filter((e) => e.target === n.id).map((e) => e.source),
      };
    });

    const spec = {
      workflow_id: workflowId,
      version_number: currentVersionNumber || 1,
      nodes: mappedNodes,
      edges: edges.map((e) => ({ source: e.source, target: e.target })),
      steps: mappedNodes,
    };

    // Preflight connection check before starting execution
    const reqProvs = Array.from(new Set(mappedNodes.map((n) => n.provider))).filter((p) => p && !isInternalProvider(p));
    const connections = useOAuthStore.getState().connections;
    const readiness = checkProviderReadiness(reqProvs, connections);

    if (!readiness.ready) {
      const missingStr = readiness.missing_connections.join(', ');
      setExecutionResult({
        ok: false,
        message: `⚠️ Connection required before execution: Missing OAuth credentials for ${missingStr}. Please connect required services before executing.`,
        status: 'BLOCKED_MISSING_CONNECTION',
        nodes_executed: 0,
        total_nodes: nodes.length,
        node_results: [],
        can_resume: false,
      });
      useExecutionStore.getState().applyRealExecutionResult('exec_blocked', 'BLOCKED_MISSING_CONNECTION', [], null);
      setIsExecuting(false);
      return;
    }

    try {
      const res = await workflowApi.executeWorkflow(spec);
      useExecutionStore.getState().applyRealExecutionResult(
        res.execution_id || 'exec_live',
        res.status || 'COMPLETED',
        res.node_results || [],
        res.final_output
      );

      const isOk = res.success && res.status === 'COMPLETED';
      const isWaiting = res.status === 'WAITING' || res.status === 'WAITING_FOR_APPROVAL' || res.status === 'PAUSED';
      const isBlocked = res.status === 'BLOCKED_MISSING_CONNECTION';
      const skippedCount = res.skipped_nodes ?? (res.node_results ? res.node_results.filter((r: any) => r.status === 'SKIPPED').length : 0);
      const skippedText = skippedCount > 0 ? ` (${skippedCount} skipped)` : '';
      setExecutionResult({
        ok: isOk,
        message: isOk
          ? `✓ Workflow [${res.execution_id || 'exec_live'}] COMPLETED — ${res.nodes_executed}/${nodes.length} nodes executed${skippedText}`
          : isBlocked
          ? `⚠️ Connection required before execution: Please connect missing OAuth services.`
          : isWaiting
          ? `⏸ Workflow [${res.execution_id || 'exec_live'}] ${res.status} — ${res.nodes_executed || 0}/${nodes.length} nodes executed${skippedText}`
          : `✕ Workflow [${res.execution_id || 'exec_live'}] ${res.status || 'FAILED'} — ${res.nodes_executed || 0}/${nodes.length} nodes executed${skippedText}`,
        execution_id: res.execution_id,
        status: res.status,
        nodes_executed: res.nodes_executed,
        total_nodes: nodes.length,
        node_results: res.node_results || [],
        final_output: res.final_output,
        can_resume: Boolean(res.can_resume),
        checkpoint_timestamp: res.checkpoint_timestamp,
      });
    } catch (err: any) {
      setExecutionResult({
        ok: false,
        message: `Execution failed: ${err.message || 'Check backend connection.'}`,
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleClear = useCallback(() => {
    setNodes([]);
    setEdges([]);
    setWorkflow({
      user_prompt: '',
      goal: '',
      services: [],
      workflow_json: {},
      execution_metadata: {},
      logs: [],
    });
    setExecutionResult(null);
    setRestoredNotice(null);
    useExecutionStore.getState().resetExecution();
  }, [setNodes, setEdges, setWorkflow, setRestoredNotice]);

  const isEmpty = nodes.length === 0;

  return (
    <DashboardLayout>
      <div className="flex flex-col h-[calc(100vh-7rem)] -m-2 sm:-m-4 p-2 sm:p-4 bg-[#0E0918]">
        {/* ── Top Studio Toolbar ── */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-2xl bg-[#13102A]/80 backdrop-blur-xl border border-[rgba(255,255,255,0.12)] shadow-xl">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 flex items-center justify-center text-[#FF6D00]">
                <Workflow className="h-4 w-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-bold tracking-tight text-white">Enterprise Visual Studio</h1>
                  {currentVersionNumber && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30 shadow-[0_0_10px_rgba(255,109,0,0.15)]">
                      v{currentVersionNumber}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Node / Edge count badge */}
            {!isEmpty && (
              <div className="hidden sm:flex items-center gap-1.5 text-[10px] font-mono bg-[#1B1728] border border-[rgba(255,255,255,0.10)] rounded-full px-3 py-1">
                <span className="text-[#FF6D00] font-bold">{nodes.length}</span>
                <span className="text-[#A098AE]">nodes</span>
                <span className="text-white/20">·</span>
                <span className="text-[#FF6D00] font-bold">{edges.length}</span>
                <span className="text-[#A098AE]">edges</span>
              </div>
            )}

            {/* Left Sidebar Mode Toggle */}
            <div className="flex rounded-xl border border-[rgba(255,255,255,0.10)] bg-[#0E0918]/80 p-1 text-xs font-semibold">
              <button
                onClick={() => setActiveTab('palette')}
                className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-1.5 ${
                  activeTab === 'palette'
                    ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-[0_0_15px_rgba(255,109,0,0.35)] font-bold'
                    : 'text-[#A098AE] hover:text-white hover:bg-[#1B1728]'
                }`}
              >
                <Cpu className="h-3.5 w-3.5" /> Node Palette
              </button>
              <button
                onClick={() => setActiveTab('ai')}
                className={`px-3 py-1 rounded-lg transition-all duration-200 flex items-center gap-1.5 ${
                  activeTab === 'ai'
                    ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-[0_0_15px_rgba(255,109,0,0.35)] font-bold'
                    : 'text-[#A098AE] hover:text-white hover:bg-[#1B1728]'
                }`}
              >
                <Sparkles className="h-3.5 w-3.5" /> AI Generator
              </button>
            </div>
          </div>

          {/* ── Action Toolbar ── */}
          <div className="flex items-center gap-1.5">
            {/* Undo / Redo */}
            <button
              onClick={undo}
              disabled={historyStack.length === 0}
              className="p-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-[#A098AE] hover:text-white hover:bg-[#231E3A] disabled:opacity-30 transition"
              title="Undo (Ctrl+Z)"
            >
              <Undo2 className="h-4 w-4" />
            </button>
            <button
              onClick={redo}
              disabled={futureStack.length === 0}
              className="p-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-[#A098AE] hover:text-white hover:bg-[#231E3A] disabled:opacity-30 transition"
              title="Redo (Ctrl+Y)"
            >
              <Redo2 className="h-4 w-4" />
            </button>

            <div className="h-4 w-px bg-[rgba(255,255,255,0.12)] mx-1" />

            {/* Copy */}
            <button
              onClick={handleCopy}
              disabled={selectedNodeIds.length === 0 && !selectedNode}
              className="p-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-[#A098AE] hover:text-white hover:bg-[#231E3A] disabled:opacity-30 transition"
              title="Copy (Ctrl+C)"
            >
              <Copy className="h-4 w-4" />
            </button>

            {/* Paste */}
            <button
              onClick={pasteNodes}
              disabled={clipboard.length === 0}
              className="p-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-[#A098AE] hover:text-white hover:bg-[#231E3A] disabled:opacity-30 transition"
              title="Paste (Ctrl+V)"
            >
              <Clipboard className="h-4 w-4" />
            </button>

            {/* Duplicate */}
            <button
              onClick={handleDuplicate}
              disabled={selectedNodeIds.length === 0 && !selectedNode}
              className="p-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-[#A098AE] hover:text-white hover:bg-[#231E3A] disabled:opacity-30 transition"
              title="Duplicate (Ctrl+D)"
            >
              <Layers className="h-4 w-4" />
            </button>

            <div className="h-4 w-px bg-[rgba(255,255,255,0.12)] mx-1" />

            {/* Auto Layout */}
            <button
              onClick={handleAutoLayout}
              disabled={isEmpty}
              className="px-3 py-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-xs font-medium text-[#A098AE] hover:text-white hover:bg-[#231E3A] transition flex items-center gap-1.5 disabled:opacity-40"
              title="Auto Layout (dagre)"
            >
              <LayoutGrid className="h-3.5 w-3.5 text-[#FF6D00]" /> Layout
            </button>

            {/* Version History */}
            <button
              onClick={() => setIsHistoryOpen(true)}
              className="px-3 py-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-xs font-medium text-[#A098AE] hover:text-white hover:bg-[#231E3A] transition flex items-center gap-1.5"
            >
              <History className="h-3.5 w-3.5 text-[#FF6D00]" /> Versions
            </button>

            {/* Execution History */}
            <button
              onClick={() => setIsExecHistoryOpen(true)}
              className="px-3 py-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-xs font-medium text-[#A098AE] hover:text-white hover:bg-[#231E3A] transition flex items-center gap-1.5"
            >
              <PlayCircle className="h-3.5 w-3.5 text-[#FF6D00]" /> Executions
            </button>

            {/* Analytics */}
            <button
              onClick={() => setIsAnalyticsOpen(true)}
              className="px-3 py-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-xs font-medium text-[#A098AE] hover:text-white hover:bg-[#231E3A] transition flex items-center gap-1.5"
            >
              <BarChart3 className="h-3.5 w-3.5 text-[#FF6D00]" /> Analytics
            </button>

            {/* Schedules & Triggers */}
            <button
              onClick={() => setIsSchedulesOpen(true)}
              className="px-3 py-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-xs font-medium text-[#A098AE] hover:text-white hover:bg-[#231E3A] transition flex items-center gap-1.5"
            >
              <Clock className="h-3.5 w-3.5 text-[#FF6D00]" /> Schedules
            </button>

            {/* JSON Spec */}
            <button
              onClick={() => setIsJSONOpen(true)}
              disabled={isEmpty}
              className="px-3 py-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] text-xs font-medium text-[#A098AE] hover:text-white hover:bg-[#231E3A] transition flex items-center gap-1.5 disabled:opacity-40"
            >
              <Code2 className="h-3.5 w-3.5" /> Spec
            </button>

            {/* Clear */}
            <button
              onClick={handleClear}
              disabled={isEmpty}
              className="px-3 py-1.5 rounded-lg border border-red-500/20 bg-red-500/10 text-xs font-medium text-red-400 hover:bg-red-500/20 transition flex items-center gap-1.5 disabled:opacity-40"
            >
              <Trash2 className="h-3.5 w-3.5" /> Clear
            </button>

            {/* Execute */}
            <button
              onClick={handleExecute}
              disabled={isEmpty || isExecuting}
              className="px-4 py-1.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl hover:opacity-95 transition flex items-center gap-2 shadow-[0_0_20px_rgba(255,109,0,0.35)] disabled:opacity-50 disabled:shadow-none"
            >
              {isExecuting ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" /> Executing…
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-current" /> Execute Workflow
                </>
              )}
            </button>
          </div>
        </div>

        {/* Restored Version Confirmation Notice Banner */}
        {restoredNotice && (
          <div className="mt-2 p-2.5 bg-[#FF6D00]/10 border border-[#FF6D00]/30 rounded-xl text-xs flex items-center justify-between text-[#FF6D00] font-medium shadow-[0_0_15px_rgba(255,109,0,0.15)]">
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 shrink-0 text-[#FF6D00]" />
              <span>{restoredNotice}</span>
            </div>
            <button
              onClick={() => setRestoredNotice(null)}
              className="p-1 rounded hover:bg-[#FF6D00]/20 transition text-[#FF6D00]"
            >
              ✕
            </button>
          </div>
        )}

        {/* Keyboard shortcuts hint bar */}
        <div className="flex items-center gap-3 py-1.5 px-2 text-[10px] text-[#A098AE] font-mono overflow-x-auto scrollbar-none border-b border-[rgba(255,255,255,0.06)]">
          {[
            ['Del', 'Delete'],
            ['Ctrl+Z', 'Undo'],
            ['Ctrl+Y', 'Redo'],
            ['Ctrl+D', 'Duplicate'],
            ['Ctrl+A', 'Select All'],
            ['Ctrl+C', 'Copy'],
            ['Ctrl+V', 'Paste'],
            ['Right-click', 'Context Menu'],
            ['Dbl-click', 'Rename'],
          ].map(([key, label]) => (
            <span key={key} className="flex items-center gap-1 shrink-0">
              <kbd className="px-1.5 py-0.5 bg-[#1B1728] border border-[rgba(255,255,255,0.10)] rounded text-[9px] text-white font-mono">{key}</kbd>
              <span className="text-[#A098AE]/60">{label}</span>
            </span>
          ))}
        </div>

        {/* Execution Result Banner & Output Inspector */}
        {executionResult && (
          <div className="mt-2 space-y-2">
            <div
              className={`p-3 text-xs rounded-xl border flex items-center gap-2 ${
                executionResult.ok
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-red-500/10 border-red-500/30 text-red-400'
              }`}
            >
              {executionResult.ok ? (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
              ) : (
                <XCircle className="h-4 w-4 shrink-0 text-red-400" />
              )}
              <span className="font-semibold">{executionResult.message}</span>
              <button
                onClick={() => setExecutionResult(null)}
                className="ml-auto p-1 rounded hover:bg-white/10 transition text-white/60 hover:text-white"
              >
                ✕
              </button>
            </div>

            {/* Live Output Inspector Card */}
            <ExecutionResultInspector
              executionResult={executionResult}
              onClose={() => setExecutionResult(null)}
              onExecuteSuccess={(res: any) => {
                const isOk = res.success && res.status === 'COMPLETED';
                const isWaiting = res.status === 'WAITING' || res.status === 'WAITING_FOR_APPROVAL' || res.status === 'PAUSED';
                const skippedCount = res.skipped_nodes ?? (res.node_results ? res.node_results.filter((r: any) => r.status === 'SKIPPED').length : 0);
                const skippedText = skippedCount > 0 ? ` (${skippedCount} skipped)` : '';
                setExecutionResult({
                  ok: isOk,
                  message: isOk
                    ? `✓ Workflow [${res.execution_id || 'exec_live'}] COMPLETED — ${res.nodes_executed}/${nodes.length} nodes executed${skippedText}`
                    : isWaiting
                    ? `⏸ Workflow [${res.execution_id || 'exec_live'}] ${res.status} — ${res.nodes_executed || 0}/${nodes.length} nodes executed${skippedText}`
                    : `✕ Workflow [${res.execution_id || 'exec_live'}] ${res.status || 'FAILED'} — ${res.nodes_executed || 0}/${nodes.length} nodes executed${skippedText}`,
                  execution_id: res.execution_id,
                  status: res.status,
                  nodes_executed: res.nodes_executed,
                  total_nodes: nodes.length,
                  node_results: res.node_results || [],
                  final_output: res.final_output,
                  can_resume: Boolean(res.can_resume),
                  checkpoint_timestamp: res.checkpoint_timestamp,
                });
              }}
            />
          </div>
        )}

        {/* ── Builder Workspace ── */}
        <div className="flex-1 flex gap-3 pt-2 overflow-hidden min-h-0">
          {/* Left Sidebar */}
          {activeTab === 'palette' ? <ConnectorPalette /> : <AIChatSidebar onOpenSchedules={() => setIsSchedulesOpen(true)} />}

          {/* Canvas */}
          <div className="flex-1 flex flex-col h-full relative">
            <WorkflowCanvas />

            {/* Empty State Overlay */}
            {isEmpty && (
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <div className="flex flex-col items-center gap-4 text-center max-w-xs p-6 rounded-2xl bg-[#13102A]/80 backdrop-blur-xl border border-[rgba(255,255,255,0.12)] shadow-2xl">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 flex items-center justify-center">
                    <MousePointerClick className="h-8 w-8 text-[#FF6D00]" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white">Canvas is empty</p>
                    <p className="text-xs text-[#A098AE] mt-1">
                      Drag nodes from the palette, or use the{' '}
                      <span className="text-[#FF6D00] font-semibold">AI Generator</span> to auto-build a workflow.
                    </p>
                  </div>
                  <div className="flex flex-col gap-1 text-[10px] text-[#A098AE]/70 font-mono">
                    <span>↑ Switch to AI Generator tab</span>
                    <span>↑ Type your workflow goal</span>
                    <span>↑ Watch the DAG build itself</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Inspector Panel */}
          {selectedNode && <NodeInspector />}
        </div>
      </div>

      <JSONViewerModal isOpen={isJSONOpen} onClose={() => setIsJSONOpen(false)} />
      <VersionHistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        currentNodes={nodes}
        currentEdges={edges}
      />
      <ExecutionHistoryModal
        isOpen={isExecHistoryOpen}
        onClose={() => setIsExecHistoryOpen(false)}
        onSelectExecution={(res) => setExecutionResult(res)}
      />
      <ExecutionAnalyticsModal
        isOpen={isAnalyticsOpen}
        onClose={() => setIsAnalyticsOpen(false)}
        onSelectExecution={(res) => setExecutionResult(res)}
      />
      <SchedulesTriggersModal
        isOpen={isSchedulesOpen}
        onClose={() => setIsSchedulesOpen(false)}
      />
    </DashboardLayout>
  );
};

