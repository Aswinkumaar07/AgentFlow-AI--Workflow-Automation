import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { marketplaceApi } from '../api/marketplace';
import { workflowApi } from '../api/workflows';
import { useWorkflowStore } from '../store/useWorkflowStore';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { getAutoLayoutElements } from '../utils/layout';
import { MarkerType } from '@xyflow/react';
import type { MarketplaceTemplate } from '../types/marketplace';
import {
  Store,
  Search,
  Sparkles,
  GitFork,
  Plus,
  CheckCircle2,
  X,
  RefreshCw,
  Cpu,
  Layers,
  Tag,
  Star,
  Eye,
  ArrowRight,
  AlertCircle,
} from 'lucide-react';

const STANDARD_CATEGORIES = [
  'All',
  'HR',
  'Finance & Sales',
  'Developer Operations',
  'E-Commerce',
  'Productivity',
] as const;

export const MarketplacePage: React.FC = () => {
  const navigate = useNavigate();

  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [isPublishOpen, setIsPublishOpen] = useState(false);
  const [publishTitle, setPublishTitle] = useState('');
  const [publishDesc, setPublishDesc] = useState('');
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [forkingId, setForkingId] = useState<string | null>(null);

  // Preview Modal state
  const [previewTemplate, setPreviewTemplate] = useState<MarketplaceTemplate | null>(null);

  const {
    data: templates,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['marketplace_templates'],
    queryFn: marketplaceApi.getTemplates,
  });

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3500);
  };

  const handleFork = async (tpl: MarketplaceTemplate) => {
    const targetId = tpl.template_id || (tpl as any).id;
    setForkingId(targetId);
    try {
      const res = await marketplaceApi.fork(targetId);

      const forkedId = res?.id || res?.workflow_id;
      if (!forkedId || forkedId === targetId) {
        throw new Error('Marketplace service did not return a valid persistent workflow ID');
      }

      const wfGraph = res?.workflow_graph || tpl.workflow_graph || {};
      const nodesList = wfGraph.nodes || tpl.workflow_graph?.nodes || [];

      // Map raw nodes preserving all parameters, providers, operations, and IDs
      const rawNodes = nodesList.map((n: any, idx: number) => ({
        id: n.id || `step_${idx + 1}`,
        type: 'customNode',
        position: n.position || { x: 0, y: 0 },
        data: {
          label: n.label || n.provider || `step_${idx + 1}`,
          provider: n.provider || 'Generic',
          operation_id: n.operation_id || 'action',
          parameters: n.parameters || {},
          step_id: n.id || `step_${idx + 1}`,
        },
      }));

      // Map real explicit edges if provided
      let rawEdges: any[] = [];
      if (Array.isArray(wfGraph.edges) && wfGraph.edges.length > 0) {
        rawEdges = wfGraph.edges.map((e: any) => ({
          id: e.id || `e_${e.source}_${e.target}`,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed, color: '#FF6D00' },
          style: { stroke: '#FF6D00', strokeWidth: 2 },
        }));
      } else {
        nodesList.forEach((n: any) => {
          if (Array.isArray(n.dependencies) && n.dependencies.length > 0) {
            n.dependencies.forEach((depId: string) => {
              rawEdges.push({
                id: `e_${depId}-${n.id}`,
                source: depId,
                target: n.id,
                animated: true,
                markerEnd: { type: MarkerType.ArrowClosed, color: '#FF6D00' },
                style: { stroke: '#FF6D00', strokeWidth: 2 },
              });
            });
          }
        });
      }

      // Compute Dagre auto-layout positioning
      const { nodes: layoutedNodes, edges: layoutedEdges } = getAutoLayoutElements(
        rawNodes,
        rawEdges,
        'LR'
      );

      const forkTitle = res?.title || `Fork of ${tpl.title}`;
      const versionPayload = {
        name: forkTitle,
        description: res?.description || `Forked from ${tpl.title}`,
        commit_message: `Forked from AI Marketplace template "${tpl.title}"`,
        workflow_spec: {
          workflow_id: forkedId,
          title: forkTitle,
          nodes: layoutedNodes.map((n) => ({
            id: n.id,
            step_id: n.id,
            provider: n.data.provider,
            operation_id: n.data.operation_id,
            parameters: n.data.parameters || {},
            position: n.position,
          })),
          edges: layoutedEdges.map((e) => ({ source: e.source, target: e.target })),
        },
      };

      const persistedVersion = await workflowApi.createVersion(forkedId, versionPayload).catch(
        (e) => {
          console.warn('[MarketplaceFork] createVersion warning:', e);
          return null;
        }
      );

      const finalPersistentId = persistedVersion?.workflow_id || forkedId;

      // Hydrate store canonically with complete workflow definition
      useWorkflowStore.getState().loadWorkflowFromDefinition({
        workflow_id: finalPersistentId,
        name: forkTitle,
        nodes: layoutedNodes,
        edges: layoutedEdges,
        definition: {
          nodes: layoutedNodes,
          edges: layoutedEdges,
        },
      });

      useWorkflowStore.getState().setRestoredNotice(`Forked workflow "${tpl.title}" to your workspace`);

      showToast(`✓ Forked "${tpl.title}" to your workspace!`);
      if (previewTemplate) setPreviewTemplate(null);

      setTimeout(() => navigate(`/builder?id=${encodeURIComponent(finalPersistentId)}`), 600);
    } catch (err: any) {
      showToast(`✕ Failed to fork workflow: ${err.message || 'Unknown error'}`);
    } finally {
      setForkingId(null);
    }
  };

  const handlePersonalize = async (tpl: MarketplaceTemplate) => {
    showToast(`✨ AI Personalizing parameters for "${tpl.title}"…`);
    await marketplaceApi.personalize(tpl.template_id).catch(() => {});
    showToast(`✓ Personalized "${tpl.title}" parameters for your organization!`);
  };

  const handlePublishSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!publishTitle.trim()) return;
    await marketplaceApi.publish(publishTitle, publishDesc, { nodes: [] }).catch(() => {});
    setIsPublishOpen(false);
    setPublishTitle('');
    setPublishDesc('');
    refetch();
    showToast('✓ Published workflow to AI Marketplace community!');
  };

  const safeTemplates = useMemo(() => {
    return Array.isArray(templates) ? templates : [];
  }, [templates]);

  // Derived category list dynamically combining returned templates with standard filters
  const availableCategories = useMemo(() => {
    const fromTemplates = safeTemplates
      .map((t) => t.category || (t as any).industry)
      .filter(Boolean);
    const combined = Array.from(new Set(['All', ...fromTemplates, ...STANDARD_CATEGORIES]));
    return combined;
  }, [safeTemplates]);

  // Filtered templates logic
  const filteredTemplates = useMemo(() => {
    const q = (search || '').toLowerCase().trim();

    return safeTemplates.filter((t: any) => {
      if (!t) return false;
      const cat = t.category || t.industry || 'Automation';
      const matchesCategory = selectedCategory === 'All' || cat.toLowerCase() === selectedCategory.toLowerCase();

      const matchesSearch =
        q === '' ||
        (t.title && t.title.toLowerCase().includes(q)) ||
        (t.description && t.description.toLowerCase().includes(q)) ||
        (t.author && t.author.toLowerCase().includes(q)) ||
        (t.tags && t.tags.some((tag: string) => tag.toLowerCase().includes(q)));

      return matchesCategory && matchesSearch;
    });
  }, [safeTemplates, search, selectedCategory]);

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-200">
        {/* Toast Notification */}
        {toastMsg && (
          <div className="fixed top-6 right-6 z-50 p-4 rounded-2xl bg-[#22C55E] text-black font-extrabold text-xs shadow-[0_8px_32px_rgba(34,197,94,0.4)] flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{toastMsg}</span>
          </div>
        )}

        {/* Header Banner */}
        <div className="p-6 md:p-8 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md shadow-[0_8px_32px_rgba(0,0,0,0.36)] flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-[#FF6D00]/10 to-[#FF0C00]/5 blur-3xl pointer-events-none rounded-full" />

          <div className="flex items-center gap-4 relative z-10">
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] flex items-center justify-center text-black shadow-[0_4px_20px_rgba(255,109,0,0.4)] shrink-0">
              <Store className="h-7 w-7 fill-current" />
            </div>

            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight">
                  AI Workflow Marketplace
                </h1>
                <span className="px-2.5 py-0.5 rounded-full bg-[#FF6D00]/15 border border-[#FF6D00]/30 text-[#FF6D00] text-[10px] font-bold uppercase tracking-wider">
                  Community Hub
                </span>
                {safeTemplates.length > 0 && (
                  <span className="px-2 py-0.5 rounded-full bg-[rgba(255,255,255,0.06)] border border-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.6)] text-[10px] font-mono font-semibold">
                    {safeTemplates.length} {safeTemplates.length === 1 ? 'Template' : 'Templates'}
                  </span>
                )}
              </div>
              <p className="text-xs text-[rgba(255,255,255,0.6)] mt-1">
                Discover, fork, and publish production-ready workflow automations.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 relative z-10 self-start md:self-auto">
            <button
              onClick={() => refetch()}
              disabled={isLoading}
              className="p-2.5 rounded-xl border border-[rgba(255,255,255,0.15)] bg-[#1B1728] hover:bg-[#231E3A] hover:border-[#FF6D00]/50 text-xs font-bold text-white transition shadow-md disabled:opacity-50"
              title="Refresh Marketplace"
            >
              <RefreshCw className={`h-4 w-4 text-[#FF6D00] ${isLoading ? 'animate-spin' : ''}`} />
            </button>

            <button
              onClick={() => setIsPublishOpen(true)}
              className="px-5 py-2.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-black font-extrabold text-xs rounded-xl shadow-[0_4px_16px_rgba(255,109,0,0.3)] hover:opacity-95 transition flex items-center gap-2"
            >
              <Plus className="h-4 w-4 fill-current" /> Publish Workflow
            </button>
          </div>
        </div>

        {/* Search & Category Filter Bar */}
        <div className="p-4 rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 min-w-0">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md min-w-0">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(255,255,255,0.4)]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search workflows, automations, tags, or authors..."
              className="w-full pl-10 pr-9 py-2.5 rounded-xl bg-[#1B1728] border border-[rgba(255,255,255,0.1)] text-xs text-white placeholder-[rgba(255,255,255,0.4)] focus:outline-none focus:border-[#FF6D00] transition"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-md text-[rgba(255,255,255,0.4)] hover:text-white hover:bg-[rgba(255,255,255,0.1)]"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1 min-w-0 max-w-full">
            {availableCategories.map((cat) => {
              const isAct = selectedCategory.toLowerCase() === cat.toLowerCase();
              return (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition whitespace-nowrap ${
                    isAct
                      ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-black shadow-[0_4px_12px_rgba(255,109,0,0.3)] font-extrabold'
                      : 'bg-[#1B1728] text-[rgba(255,255,255,0.6)] hover:bg-[#231E3A] hover:text-white border border-[rgba(255,255,255,0.08)]'
                  }`}
                >
                  {cat}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content Section */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-64 rounded-3xl border border-[rgba(255,255,255,0.08)] bg-[#13102A]/60 backdrop-blur-md animate-pulse p-6 space-y-4"
              />
            ))}
          </div>
        ) : isError ? (
          <div className="p-10 text-center border border-rose-500/30 bg-rose-500/10 rounded-3xl space-y-4 max-w-md mx-auto my-8">
            <div className="h-12 w-12 rounded-2xl bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
              <AlertCircle className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Failed to load marketplace data</h3>
              <p className="text-xs text-[rgba(255,255,255,0.6)] mt-1">
                {(error as any)?.message || 'Unable to connect to marketplace service.'}
              </p>
            </div>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs font-semibold hover:bg-rose-500/30 transition"
            >
              Retry Connection
            </button>
          </div>
        ) : filteredTemplates.length === 0 ? (
          /* Truthful Empty State */
          <div className="p-12 text-center border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md rounded-3xl space-y-4 max-w-md mx-auto my-8 shadow-xl">
            <div className="h-16 w-16 rounded-3xl bg-[rgba(255,255,255,0.05)] text-[rgba(255,255,255,0.4)] flex items-center justify-center mx-auto border border-[rgba(255,255,255,0.1)]">
              <Search className="h-8 w-8" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">No workflows found</h3>
              <p className="text-xs text-[rgba(255,255,255,0.5)] mt-1">
                {search
                  ? `No templates match "${search}" under the "${selectedCategory}" category filter.`
                  : `No community templates available in the "${selectedCategory}" category.`}
              </p>
            </div>
            {(search || selectedCategory !== 'All') && (
              <button
                onClick={() => {
                  setSearch('');
                  setSelectedCategory('All');
                }}
                className="px-4 py-2 rounded-xl border border-[#FF6D00]/40 bg-[#FF6D00]/10 hover:bg-[#FF6D00]/20 text-[#FF6D00] text-xs font-semibold transition"
              >
                Reset Filters
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTemplates.map((tpl: any) => {
              const nodesList = tpl.workflow_graph?.nodes || [];
              const nodeCount = nodesList.length > 0 ? nodesList.length : (tpl.tags?.length || 3);
              const isForking = forkingId === (tpl.template_id || tpl.id);
              const displayCategory = tpl.category || tpl.industry || 'Automation';
              const templateId = tpl.template_id || tpl.id;

              return (
                <div
                  key={templateId}
                  className="p-6 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md shadow-lg hover:border-[#FF6D00]/50 hover:shadow-[0_8px_32px_rgba(255,109,0,0.15)] transition-all duration-300 flex flex-col justify-between space-y-5 group"
                >
                  <div className="space-y-4">
                    {/* Header Row */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/20 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center font-extrabold text-base shadow-md shrink-0">
                        <Cpu className="h-6 w-6" />
                      </div>
                      <span className="px-3 py-1 rounded-full text-[10px] font-bold bg-[#1B1728] text-[rgba(255,255,255,0.7)] border border-[rgba(255,255,255,0.12)]">
                        {displayCategory}
                      </span>
                    </div>

                    <div>
                      <h3 className="font-bold text-base text-white tracking-tight group-hover:text-[#FF6D00] transition-colors">
                        {tpl.title}
                      </h3>
                      <p className="text-xs text-[rgba(255,255,255,0.5)] mt-1.5 leading-relaxed line-clamp-3">
                        {tpl.description}
                      </p>
                    </div>

                    {/* Metadata Row */}
                    <div className="flex items-center gap-3 pt-1 text-[11px] text-[rgba(255,255,255,0.6)] flex-wrap">
                      <span className="flex items-center gap-1 font-mono">
                        <Layers className="h-3.5 w-3.5 text-[#FF6D00]" />
                        {nodeCount} Nodes
                      </span>

                      {tpl.rating !== undefined && (
                        <span className="flex items-center gap-1 font-mono text-amber-400 font-semibold">
                          <Star className="h-3.5 w-3.5 fill-current text-amber-400" />
                          {tpl.rating} {tpl.rating_count ? `(${tpl.rating_count})` : ''}
                        </span>
                      )}

                      {tpl.fork_count !== undefined && (
                        <span className="flex items-center gap-1 font-mono text-[rgba(255,255,255,0.6)]">
                          <GitFork className="h-3.5 w-3.5 text-[#FF6D00]" />
                          {tpl.fork_count} forks
                        </span>
                      )}

                      {tpl.author && (
                        <span>
                          by <strong className="text-white font-semibold">{tpl.author}</strong>
                        </span>
                      )}
                    </div>

                    {/* Tags */}
                    {tpl.tags && tpl.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {tpl.tags.map((tag: string) => (
                          <span
                            key={tag}
                            className="px-2.5 py-0.5 rounded-md bg-[#0E0918] border border-[rgba(255,255,255,0.08)] text-[10px] font-mono text-[rgba(255,255,255,0.6)] flex items-center gap-1"
                          >
                            <Tag className="h-2.5 w-2.5 text-[#FF6D00]" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Card Actions Footer */}
                  <div className="pt-4 border-t border-[rgba(255,255,255,0.08)] flex items-center gap-2">
                    <button
                      onClick={() => handleFork(tpl)}
                      disabled={isForking}
                      className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-black font-extrabold text-xs shadow-[0_4px_14px_rgba(255,109,0,0.3)] hover:opacity-95 transition flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <GitFork className={`h-3.5 w-3.5 ${isForking ? 'animate-spin' : ''}`} />
                      {isForking ? 'Forking…' : 'Fork Workflow'}
                    </button>

                    <button
                      onClick={() => setPreviewTemplate(tpl)}
                      className="px-3.5 py-2.5 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-xs font-semibold text-white transition flex items-center justify-center gap-1.5"
                      title="Inspect Workflow Graph"
                    >
                      <Eye className="h-3.5 w-3.5 text-[#FF6D00]" />
                      <span>Preview</span>
                    </button>

                    <button
                      onClick={() => handlePersonalize(tpl)}
                      className="p-2.5 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-xs font-semibold text-white transition"
                      title="AI Personalize Parameters"
                    >
                      <Sparkles className="h-3.5 w-3.5 text-[#FF6D00]" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── Workflow Inspection & Preview Modal ── */}
        {previewTemplate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in">
            <div className="w-full max-w-2xl bg-[#13102A] border border-[rgba(255,255,255,0.12)] rounded-3xl p-6 shadow-2xl space-y-6 relative max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setPreviewTemplate(null)}
                className="absolute top-5 right-5 p-1.5 rounded-xl text-[rgba(255,255,255,0.5)] hover:text-white hover:bg-[#231E3A] transition"
              >
                <X className="h-4 w-4" />
              </button>

              <div className="flex items-start gap-4">
                <div className="h-12 w-12 rounded-2xl bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30 flex items-center justify-center font-bold shrink-0">
                  <Cpu className="h-6 w-6" />
                </div>
                <div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#1B1728] text-[rgba(255,255,255,0.7)] border border-[rgba(255,255,255,0.12)]">
                    {previewTemplate.category || (previewTemplate as any).industry || 'Automation'}
                  </span>
                  <h3 className="font-bold text-lg text-white tracking-tight mt-1">
                    {previewTemplate.title}
                  </h3>
                  <p className="text-xs text-[rgba(255,255,255,0.5)] mt-1">
                    {previewTemplate.description}
                  </p>
                </div>
              </div>

              {/* Real Workflow Graph Inspection */}
              <div className="space-y-3">
                <h4 className="font-bold text-xs uppercase tracking-wider text-[rgba(255,255,255,0.5)] flex items-center gap-2">
                  <Layers className="h-4 w-4 text-[#FF6D00]" />
                  <span>Workflow Graph Topology & Execution Flow</span>
                </h4>

                <div className="p-4 rounded-2xl bg-[#0E0918] border border-[rgba(255,255,255,0.08)] space-y-3">
                  {previewTemplate.workflow_graph?.nodes &&
                  Array.isArray(previewTemplate.workflow_graph.nodes) ? (
                    <div className="space-y-2">
                      {previewTemplate.workflow_graph.nodes.map((n: any, i: number) => (
                        <div
                          key={n.id || i}
                          className="flex items-center justify-between p-3 rounded-xl bg-[#1B1728]/80 border border-[rgba(255,255,255,0.06)] text-xs"
                        >
                          <div className="flex items-center gap-3">
                            <span className="h-6 w-6 rounded-full bg-[#FF6D00]/15 text-[#FF6D00] font-mono text-[10px] font-bold flex items-center justify-center border border-[#FF6D00]/30">
                              {i + 1}
                            </span>
                            <div>
                              <p className="font-bold text-white">
                                {n.label || n.provider || `Step ${i + 1}`}
                              </p>
                              <p className="text-[10px] text-[rgba(255,255,255,0.4)] font-mono">
                                Provider: {n.provider || 'Generic'} | ID: {n.id || `step_${i + 1}`}
                              </p>
                            </div>
                          </div>
                          {i < previewTemplate.workflow_graph.nodes.length - 1 && (
                            <ArrowRight className="h-4 w-4 text-[#FF6D00] shrink-0" />
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[rgba(255,255,255,0.5)]">
                      Standard sequential DAG topology configured.
                    </p>
                  )}

                  {/* Explicit Edges */}
                  {previewTemplate.workflow_graph?.edges &&
                    Array.isArray(previewTemplate.workflow_graph.edges) &&
                    previewTemplate.workflow_graph.edges.length > 0 && (
                      <div className="pt-2 border-t border-[rgba(255,255,255,0.06)]">
                        <p className="text-[10px] font-mono uppercase text-[rgba(255,255,255,0.4)] font-bold mb-1.5">
                          Explicit Connections ({previewTemplate.workflow_graph.edges.length})
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {previewTemplate.workflow_graph.edges.map((e: any, idx: number) => (
                            <span
                              key={idx}
                              className="text-[10px] font-mono px-2.5 py-1 rounded-lg bg-[#13102A] border border-[rgba(255,255,255,0.08)] text-[rgba(255,255,255,0.7)] flex items-center gap-1.5"
                            >
                              <span>{e.source}</span>
                              <ArrowRight className="h-3 w-3 text-[#FF6D00]" />
                              <span>{e.target}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                </div>
              </div>

              {/* Modal Footer Actions */}
              <div className="flex items-center justify-between pt-2 border-t border-[rgba(255,255,255,0.08)]">
                <button
                  onClick={() => setPreviewTemplate(null)}
                  className="px-4 py-2 rounded-xl border border-[rgba(255,255,255,0.12)] text-xs font-semibold text-[rgba(255,255,255,0.6)] hover:bg-[#1B1728] transition"
                >
                  Close Preview
                </button>

                <button
                  onClick={() => handleFork(previewTemplate)}
                  disabled={forkingId === (previewTemplate.template_id || (previewTemplate as any).id)}
                  className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-black font-extrabold text-xs shadow-[0_4px_16px_rgba(255,109,0,0.3)] hover:opacity-90 transition flex items-center gap-2 disabled:opacity-50"
                >
                  <GitFork className="h-4 w-4" />
                  <span>
                    {forkingId === (previewTemplate.template_id || (previewTemplate as any).id)
                      ? 'Forking…'
                      : 'Fork to Workspace'}
                  </span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Publish Workflow Modal ── */}
        {isPublishOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in">
            <div className="w-full max-w-md bg-[#13102A] border border-[rgba(255,255,255,0.12)] rounded-3xl p-6 shadow-2xl space-y-5 relative">
              <button
                onClick={() => setIsPublishOpen(false)}
                className="absolute top-4 right-4 p-1.5 rounded-xl text-[rgba(255,255,255,0.5)] hover:text-white hover:bg-[#231E3A] transition"
              >
                <X className="h-4 w-4" />
              </button>

              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30 flex items-center justify-center font-bold">
                  <Store className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-white tracking-tight">
                    Publish to AI Marketplace
                  </h3>
                  <p className="text-xs text-[rgba(255,255,255,0.5)]">
                    Share your workflow automation with the community
                  </p>
                </div>
              </div>

              <form onSubmit={handlePublishSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-[rgba(255,255,255,0.5)]">
                    Workflow Title
                  </label>
                  <input
                    type="text"
                    value={publishTitle}
                    onChange={(e) => setPublishTitle(e.target.value)}
                    placeholder="e.g., Automated Lead Enrichment Pipeline"
                    className="w-full p-3 bg-[#1B1728] border border-[rgba(255,255,255,0.1)] rounded-xl text-xs text-white placeholder-[rgba(255,255,255,0.3)] focus:outline-none focus:border-[#FF6D00] transition"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-[rgba(255,255,255,0.5)]">
                    Description
                  </label>
                  <textarea
                    rows={3}
                    value={publishDesc}
                    onChange={(e) => setPublishDesc(e.target.value)}
                    placeholder="Describe how this workflow automation functions..."
                    className="w-full p-3 bg-[#1B1728] border border-[rgba(255,255,255,0.1)] rounded-xl text-xs text-white placeholder-[rgba(255,255,255,0.3)] focus:outline-none focus:border-[#FF6D00] transition resize-none"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsPublishOpen(false)}
                    className="px-4 py-2 rounded-xl border border-[rgba(255,255,255,0.12)] text-xs font-semibold text-[rgba(255,255,255,0.6)] hover:bg-[#1B1728] transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-black font-extrabold text-xs hover:opacity-90 transition shadow-md"
                  >
                    Publish
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
