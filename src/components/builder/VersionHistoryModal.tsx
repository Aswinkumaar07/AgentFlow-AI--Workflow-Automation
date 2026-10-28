import React, { useEffect, useState } from 'react';
import { useWorkflowStore, type WorkflowVersion } from '../../store/useWorkflowStore';
import { History, X, Save, RotateCcw, Eye, CheckCircle2 } from 'lucide-react';

interface VersionHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowId?: string;
  currentNodes?: any[];
  currentEdges?: any[];
}

export const VersionHistoryModal: React.FC<VersionHistoryModalProps> = ({
  isOpen,
  onClose,
  workflowId,
  currentNodes,
  currentEdges,
}) => {
  const {
    workflowId: storeWorkflowId,
    nodes: storeNodes,
    edges: storeEdges,
    savedVersions,
    currentVersionNumber,
    fetchVersions,
    saveVersion,
    restoreVersion,
  } = useWorkflowStore();

  const [versionName, setVersionName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [selectedViewVersion, setSelectedViewVersion] = useState<WorkflowVersion | null>(null);

  const activeWorkflowId = workflowId || storeWorkflowId;

  useEffect(() => {
    if (isOpen) {
      setSaveError(null);
      fetchVersions(activeWorkflowId);
    }
  }, [isOpen, activeWorkflowId, fetchVersions]);

  if (!isOpen) return null;

  const targetNodes = currentNodes && currentNodes.length > 0 ? currentNodes : storeNodes;
  const targetEdges = currentEdges && currentEdges.length > 0 ? currentEdges : storeEdges;
  const isCanvasEmpty = !targetNodes || targetNodes.length === 0;

  const handleCreateVersion = async () => {
    if (!versionName.trim() || isSaving) return;
    if (isCanvasEmpty) {
      setSaveError('Cannot save empty workflow snapshot. Canvas has 0 nodes.');
      return;
    }
    const storeState = useWorkflowStore.getState();
    console.log(
      `[AI-26 DIAGNOSTIC][1. BROWSER SAVE CLICK] target_nodes=${targetNodes.length} target_edges=${targetEdges.length} store_nodes=${storeState.nodes.length} store_edges=${storeState.edges.length}`
    );
    setIsSaving(true);
    setSaveError(null);
    try {
      await saveVersion(
        versionName.trim(),
        'Updated workflow definition',
        targetNodes,
        targetEdges,
        activeWorkflowId
      );
      setVersionName('');
      await fetchVersions(activeWorkflowId);
    } catch (err: any) {
      console.error('[AI-26 DIAGNOSTIC] saveVersion error:', err);
      setSaveError(err?.message || 'Failed to save version snapshot');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRestore = async (v: WorkflowVersion) => {
    await restoreVersion(v);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-xl bg-[#13102A]/95 border border-[rgba(255,255,255,0.12)] rounded-2xl shadow-2xl backdrop-blur-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 border-b border-[rgba(255,255,255,0.10)] flex items-center justify-between bg-[#1B1728]/50">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center font-bold">
              <History className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">Workflow Version History</h3>
              <p className="text-[10px] text-[#A098AE]">Snapshot history & instant point-in-time restore</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Save Version Input */}
        <div className="p-4 border-b border-[rgba(255,255,255,0.10)] bg-[#0E0918]/60 space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={versionName}
              onChange={(e) => {
                setVersionName(e.target.value);
                if (saveError) setSaveError(null);
              }}
              placeholder="Name new version snapshot (e.g. Version 2 - Added Slack alert)..."
              className="flex-1 px-3.5 py-2 text-xs bg-[#1B1728] border border-[rgba(255,255,255,0.12)] text-white placeholder-[#7A748E] rounded-xl focus:outline-none focus:border-[#FF6D00]"
            />
            <button
              onClick={handleCreateVersion}
              disabled={!versionName.trim() || isSaving || isCanvasEmpty}
              className="px-4 py-2 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl hover:opacity-95 transition flex items-center gap-1.5 shadow-[0_0_15px_rgba(255,109,0,0.30)] disabled:opacity-50 disabled:shadow-none cursor-pointer"
            >
              <Save className="h-3.5 w-3.5" /> {isSaving ? 'Saving…' : 'Save Version'}
            </button>
          </div>

          {isCanvasEmpty ? (
            <p className="text-[11px] text-amber-400/90 flex items-center gap-1 font-mono">
              ⚠️ Cannot save snapshot: Canvas is empty. Add or generate nodes before saving a version.
            </p>
          ) : saveError ? (
            <p className="text-[11px] text-red-400 flex items-center gap-1 font-mono">
              ⚠️ {saveError}
            </p>
          ) : null}
        </div>

        {/* Versions List */}
        <div className="p-4 flex-1 overflow-y-auto space-y-2.5 scrollbar-thin scrollbar-thumb-[#231E3A]">
          {savedVersions.length === 0 ? (
            <div className="text-center py-10 space-y-2">
              <History className="h-8 w-8 text-[#A098AE]/40 mx-auto" />
              <p className="text-xs text-[#A098AE] font-semibold">
                No version snapshots recorded yet.
              </p>
              <p className="text-[11px] text-[#7A748E]">
                Click <span className="text-[#FF6D00] font-bold">Save Version</span> or run an execution to create version 1.
              </p>
            </div>
          ) : (
            savedVersions.map((v) => {
              const verNum = v.version_number ?? (parseInt(v.version_id.replace(/\D/g, ''), 10) || 1);
              const isCurrent = currentVersionNumber === verNum || (savedVersions[0].version_id === v.version_id && !currentVersionNumber);
              const nodeCount = v.node_count ?? (v.nodes ? v.nodes.length : 0);

              return (
                <div
                  key={v.version_id}
                  className={`p-4 rounded-xl border transition ${
                    isCurrent
                      ? 'bg-[#1B1728] border-[#FF6D00]/60 shadow-[0_0_15px_rgba(255,109,0,0.15)]'
                      : 'bg-[#13102A]/80 border-[rgba(255,255,255,0.08)] hover:border-[#FF6D00]/30 hover:bg-[#1B1728]'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30 font-mono">
                          v{verNum}
                        </span>
                        {isCurrent && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 font-mono">
                            <CheckCircle2 className="h-3 w-3" /> Current
                          </span>
                        )}
                        <span className="text-xs font-bold text-white">{v.name || `Workflow Snapshot v${verNum}`}</span>
                      </div>
                      <p className="text-[11px] text-[#A098AE] font-mono">
                        {v.saved_at ? new Date(v.saved_at).toLocaleString() : 'Just now'} • {nodeCount} node{nodeCount === 1 ? '' : 's'}
                      </p>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      <button
                        onClick={() => setSelectedViewVersion(selectedViewVersion?.version_id === v.version_id ? null : v)}
                        className="px-2.5 py-1 bg-[#0E0918] hover:bg-[#231E3A] border border-[rgba(255,255,255,0.10)] text-[11px] font-medium text-[#A098AE] hover:text-white rounded-lg transition flex items-center gap-1 cursor-pointer"
                      >
                        <Eye className="h-3 w-3 text-[#FF6D00]" /> View
                      </button>
                      <button
                        onClick={() => handleRestore(v)}
                        className="px-3 py-1 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-[11px] font-bold rounded-lg hover:opacity-90 transition flex items-center gap-1 shadow-sm cursor-pointer"
                      >
                        <RotateCcw className="h-3 w-3" /> Restore
                      </button>
                    </div>
                  </div>

                  {/* Inline Spec Viewer */}
                  {selectedViewVersion?.version_id === v.version_id && (
                    <div className="mt-3 p-3 bg-[#0E0918] rounded-xl border border-[rgba(255,255,255,0.10)] text-[11px] font-mono space-y-1.5">
                      <div className="flex justify-between text-[#A098AE] font-semibold text-[10px]">
                        <span>Version ID: {v.version_id}</span>
                        <span>{nodeCount} Nodes</span>
                      </div>
                      <pre className="p-2.5 bg-black/40 text-emerald-400 rounded-lg border border-[rgba(255,255,255,0.08)] max-h-40 overflow-auto text-[10px] scrollbar-thin">
                        {JSON.stringify(v.nodes || [], null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
