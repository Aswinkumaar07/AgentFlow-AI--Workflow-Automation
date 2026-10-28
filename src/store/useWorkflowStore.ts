import { create } from 'zustand';
import type { Node, Edge } from '@xyflow/react';
import type { AIGenerateResponse } from '../types/ai';
import { workflowApi } from '../api/workflows';
import { getAutoLayoutElements } from '../utils/layout';

export interface WorkflowVersion {
  version_id: string;
  workflow_id?: string;
  version_number?: number;
  saved_at?: string;
  created_at?: number | string;
  name: string;
  nodes: Node[];
  edges: Edge[];
  node_count?: number;
  edge_count?: number;
  commit_message?: string;
}

interface WorkflowState {
  workflowId: string;
  currentVersionNumber: number | null;
  restoredNotice: string | null;
  nodes: Node[];
  edges: Edge[];
  generatedWorkflow: AIGenerateResponse | null;
  isGenerating: boolean;
  selectedNode: Node | null;
  selectedEdgeIds: string[];
  historyPrompts: string[];
  historyStack: Array<{ nodes: Node[]; edges: Edge[] }>;
  futureStack: Array<{ nodes: Node[]; edges: Edge[] }>;
  savedVersions: WorkflowVersion[];
  clipboard: Node[];

  databaseWorkflowId?: string | null;
  setWorkflowId: (id: string) => void;
  setDatabaseWorkflowId: (id: string | null) => void;
  setRestoredNotice: (msg: string | null) => void;
  setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void;
  setWorkflow: (workflow: AIGenerateResponse) => void;
  setIsGenerating: (loading: boolean) => void;
  setSelectedNode: (node: Node | null) => void;
  setSelectedEdgeIds: (ids: string[]) => void;
  addPromptHistory: (prompt: string) => void;
  addNode: (node: Node) => void;
  updateNodeData: (nodeId: string, newData: Record<string, any>) => void;
  deleteNode: (nodeId: string) => void;
  deleteSelected: (nodeIds: string[], edgeIds: string[]) => void;
  duplicateNode: (nodeId: string) => void;
  copySelectedNodes: (nodeIds: string[]) => void;
  pasteNodes: () => void;
  pushHistory: () => void;
  undo: () => void;
  redo: () => void;
  fetchVersions: (targetWorkflowId?: string) => Promise<void>;
  saveVersion: (name: string, commitMessage?: string, overrideNodes?: Node[], overrideEdges?: Edge[], targetWorkflowId?: string) => Promise<void>;
  restoreVersion: (versionItem: any) => Promise<void>;
  loadWorkflowFromDefinition: (wf: any) => void;
  loadWorkflowFromBackend: (id: string) => Promise<void>;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  workflowId: 'wf_studio_1',
  currentVersionNumber: null,
  restoredNotice: null,
  nodes: [],
  edges: [],
  generatedWorkflow: null,
  isGenerating: false,
  selectedNode: null,
  selectedEdgeIds: [],
  historyPrompts: [
    'When a Gmail invoice arrives, upload it to Google Drive, then notify Slack.',
    'Sync new GitHub issues to Notion and post an alert on Discord.',
    'Charge Stripe customer and dispatch a webhook notification.',
  ],
  historyStack: [],
  futureStack: [],
  savedVersions: [],
  clipboard: [],
  databaseWorkflowId: null,

  setWorkflowId: (workflowId) => set({ workflowId }),
  setDatabaseWorkflowId: (databaseWorkflowId) => set({ databaseWorkflowId }),
  setRestoredNotice: (restoredNotice) => set({ restoredNotice }),

  setNodes: (updater) =>
    set((state) => {
      const nextNodes = typeof updater === 'function' ? updater(state.nodes) : updater;
      let nextSelected = state.selectedNode;
      if (nextSelected) {
        const selectedId = nextSelected.id;
        const found = nextNodes.find((n) => n.id === selectedId);
        if (found) {
          nextSelected = found;
        }
      }
      return { nodes: nextNodes, selectedNode: nextSelected };
    }),
  setEdges: (updater) =>
    set((state) => {
      const nextEdges = typeof updater === 'function' ? updater(state.edges) : updater;
      return { edges: nextEdges };
    }),
  setWorkflow: (workflow) => {
    let parsedNodes: Node[] = [];
    let parsedEdges: Edge[] = [];

    const wfJson = workflow?.workflow_json;
    const stepsList = (wfJson?.nodes && Array.isArray(wfJson.nodes) && wfJson.nodes.length > 0)
      ? null
      : (workflow?.steps || (wfJson as any)?.steps);

    if (wfJson?.nodes && Array.isArray(wfJson.nodes) && wfJson.nodes.length > 0) {
      parsedNodes = wfJson.nodes.map((n: any, idx: number) => {
        const rawData = n.data && typeof n.data === 'object' ? n.data : {};
        const parameters = n.parameters ?? rawData.parameters ?? {};
        return {
          id: n.id || `step_${idx + 1}`,
          type: 'customNode',
          position: n.position || { x: 250, y: idx * 160 + 50 },
          data: {
            label: rawData.label || n.label || n.provider || n.id,
            provider: rawData.provider || n.provider || 'Generic',
            operation_id: rawData.operation_id || n.operation_id || 'generic.http.request',
            step_id: rawData.step_id || n.id || `step_${idx + 1}`,
            ...rawData,
            parameters,
          },
        };
      });
      if (wfJson.edges && Array.isArray(wfJson.edges)) {
        parsedEdges = wfJson.edges.map((e: any) => ({
          id: e.id || `e_${e.source}_${e.target}`,
          source: e.source,
          target: e.target,
          animated: true,
        }));
      }
    } else if (Array.isArray(stepsList) && stepsList.length > 0) {
      parsedNodes = stepsList.map((step: any, idx: number) => ({
        id: step.step_id || step.id || `step_${idx + 1}`,
        type: 'customNode',
        position: { x: 250, y: idx * 160 + 50 },
        data: {
          label: step.provider || step.label || step.id,
          provider: step.provider || 'Generic',
          operation_id: step.operation_id || 'generic.http.request',
          parameters: step.parameters || {},
          step_id: step.step_id || step.id,
        },
      }));
      stepsList.forEach((step: any) => {
        if (step.dependencies) {
          step.dependencies.forEach((depId: string) => {
            parsedEdges.push({
              id: `e_${depId}-${step.step_id || step.id}`,
              source: depId,
              target: step.step_id || step.id,
              animated: true,
            });
          });
        }
      });
    }

    const targetWfId =
      (workflow as any)?.workflow_id ||
      (workflow as any)?.workflow_json?.workflow_id ||
      get().workflowId ||
      'wf_studio_1';


    console.log(`[AI30-REFRESH] setWorkflow workflowId=${targetWfId} parsedNodes=${parsedNodes.length} parsedEdges=${parsedEdges.length}`);

    if (parsedNodes.length > 0) {
      const { nodes: layoutedNodes, edges: layoutedEdges } = getAutoLayoutElements(parsedNodes, parsedEdges);
      console.log(`[AI30-REFRESH] setWorkflow layoutedNodes=${layoutedNodes.length} layoutedEdges=${layoutedEdges.length}`);
      set({
        workflowId: targetWfId,
        databaseWorkflowId: (workflow as any)?.id || null,
        generatedWorkflow: workflow,
        nodes: layoutedNodes,
        edges: layoutedEdges,
        currentVersionNumber: 1,
        savedVersions: [],
        restoredNotice: null,
      });
      get().fetchVersions(targetWfId);
    } else {
      set({
        workflowId: targetWfId,
        databaseWorkflowId: (workflow as any)?.id || null,
        generatedWorkflow: workflow,
        currentVersionNumber: 1,
        savedVersions: [],
        restoredNotice: null,
      });
      get().fetchVersions(targetWfId);
    }
  },

  setIsGenerating: (isGenerating) => set({ isGenerating }),
  setSelectedNode: (selectedNode) => set({ selectedNode }),
  setSelectedEdgeIds: (selectedEdgeIds) => set({ selectedEdgeIds }),
  addPromptHistory: (prompt) =>
    set((state) => ({
      historyPrompts: [prompt, ...state.historyPrompts.filter((p) => p !== prompt)],
    })),

  pushHistory: () => {
    const { nodes, edges, historyStack } = get();
    set({
      historyStack: [...historyStack.slice(-49), { nodes, edges }],
      futureStack: [],
    });
  },

  addNode: (node) => {
    get().pushHistory();
    set((state) => ({ nodes: [...state.nodes, node] }));
  },

  updateNodeData: (nodeId, newData) => {
    get().pushHistory();
    set((state) => {
      const nextNodes = state.nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, ...newData } } : n
      );
      let nextSelected = state.selectedNode;
      if (nextSelected && nextSelected.id === nodeId) {
        const found = nextNodes.find((n) => n.id === nodeId);
        if (found) {
          nextSelected = found;
        }
      }
      return { nodes: nextNodes, selectedNode: nextSelected };
    });
  },

  deleteNode: (nodeId) => {
    get().pushHistory();
    set((state) => ({
      nodes: state.nodes.filter((n) => !nodeId.includes(n.id)),
      edges: state.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
      selectedNode: state.selectedNode?.id === nodeId ? null : state.selectedNode,
    }));
  },

  deleteSelected: (nodeIds, edgeIds) => {
    if (nodeIds.length === 0 && edgeIds.length === 0) return;
    get().pushHistory();
    set((state) => ({
      nodes: state.nodes.filter((n) => !nodeIds.includes(n.id)),
      edges: state.edges.filter(
        (e) =>
          !edgeIds.includes(e.id) &&
          !nodeIds.includes(e.source) &&
          !nodeIds.includes(e.target)
      ),
      selectedNode:
        state.selectedNode && nodeIds.includes(state.selectedNode.id)
          ? null
          : state.selectedNode,
      selectedEdgeIds: [],
    }));
  },

  duplicateNode: (nodeId) => {
    const { nodes } = get();
    const target = nodes.find((n) => n.id === nodeId);
    if (!target) return;

    get().pushHistory();
    const newNode: Node = {
      ...target,
      id: `step_${Math.random().toString(36).substring(2, 7)}`,
      position: { x: target.position.x + 40, y: target.position.y + 40 },
      selected: false,
    };
    set((state) => ({ nodes: [...state.nodes, newNode] }));
  },

  copySelectedNodes: (nodeIds) => {
    const { nodes } = get();
    const toCopy = nodes.filter((n) => nodeIds.includes(n.id));
    set({ clipboard: toCopy });
  },

  pasteNodes: () => {
    const { clipboard } = get();
    if (clipboard.length === 0) return;

    get().pushHistory();
    const pasted: Node[] = clipboard.map((n) => ({
      ...n,
      id: `step_${Math.random().toString(36).substring(2, 7)}`,
      position: { x: n.position.x + 60, y: n.position.y + 60 },
      selected: false,
    }));
    set((state) => ({ nodes: [...state.nodes, ...pasted] }));
  },

  undo: () => {
    const { historyStack, nodes, edges, futureStack } = get();
    if (historyStack.length === 0) return;

    const previous = historyStack[historyStack.length - 1];
    set({
      nodes: previous.nodes,
      edges: previous.edges,
      historyStack: historyStack.slice(0, -1),
      futureStack: [...futureStack.slice(-49), { nodes, edges }],
    });
  },

  redo: () => {
    const { futureStack, nodes, edges, historyStack } = get();
    if (futureStack.length === 0) return;

    const next = futureStack[futureStack.length - 1];
    set({
      nodes: next.nodes,
      edges: next.edges,
      futureStack: futureStack.slice(0, -1),
      historyStack: [...historyStack.slice(-49), { nodes, edges }],
    });
  },

  fetchVersions: async (targetWorkflowId?: string) => {
    const workflowId = targetWorkflowId || get().workflowId;
    try {
      const list = await workflowApi.getVersions(workflowId);
      const formatted: WorkflowVersion[] = list.map((item: any) => ({
        version_id: item.version_id,
        workflow_id: item.workflow_id || workflowId,
        version_number: item.version_number,
        saved_at: new Date((item.created_at || Date.now() / 1000) * 1000).toISOString(),
        created_at: item.created_at,
        name: item.name || `Workflow Version v${item.version_number}`,
        nodes: item.nodes || item.workflow_spec?.nodes || item.workflow_spec?.steps || [],
        edges: item.edges || item.workflow_spec?.edges || [],
        node_count: item.node_count ?? (item.nodes ? item.nodes.length : (item.workflow_spec?.nodes?.length || item.workflow_spec?.steps?.length || 0)),
        edge_count: item.edge_count ?? (item.edges ? item.edges.length : (item.workflow_spec?.edges?.length || 0)),
        commit_message: item.commit_message,
      }));
      set({ savedVersions: formatted });
    } catch {
      // keep current savedVersions
    }
  },

  saveVersion: async (name, commitMessage = 'Updated workflow definition', overrideNodes?: Node[], overrideEdges?: Edge[], targetWorkflowId?: string) => {
    let { nodes, edges, workflowId: currentWfId, savedVersions, generatedWorkflow } = get();
    const workflowId = targetWorkflowId || currentWfId;

    console.log(
      `[AI-26 DIAGNOSTIC][2. STORE SAVE_VERSION ENTER] workflowId=${workflowId} initial_nodes=${nodes.length} initial_edges=${edges.length} override_nodes=${overrideNodes?.length ?? 'none'} override_edges=${overrideEdges?.length ?? 'none'}`
    );

    if (overrideNodes && overrideNodes.length > 0) {
      nodes = overrideNodes;
      edges = overrideEdges || edges;
    }

    // Fallback: If store nodes are empty, derive from generatedWorkflow if available
    if (nodes.length === 0 && generatedWorkflow) {
      console.log('[AI-26 DIAGNOSTIC][2. STORE SAVE_VERSION FALLBACK] Attempting derivation from generatedWorkflow...');
      let wfJson = generatedWorkflow.workflow_json;
      if (typeof wfJson === 'string') {
        try { wfJson = JSON.parse(wfJson); } catch {}
      }
      const candidateNodes = wfJson?.nodes || (generatedWorkflow as any)?.nodes || [];
      const candidateEdges = wfJson?.edges || (generatedWorkflow as any)?.edges || [];
      const candidateSteps = generatedWorkflow.steps || (wfJson as any)?.steps || [];

      if (Array.isArray(candidateNodes) && candidateNodes.length > 0) {
        nodes = candidateNodes;
        edges = Array.isArray(candidateEdges) ? candidateEdges : [];
      } else if (Array.isArray(candidateSteps) && candidateSteps.length > 0) {
        nodes = candidateSteps.map((s: any, idx: number) => ({
          id: s.step_id || s.id || `step_${idx + 1}`,
          type: 'customNode',
          position: { x: 250, y: idx * 160 + 50 },
          data: {
            label: s.provider || s.label || s.id,
            provider: s.provider || 'Generic',
            operation_id: s.operation_id || 'generic.http.request',
            parameters: s.parameters || {},
            step_id: s.step_id || s.id,
          },
        }));
        edges = [];
        candidateSteps.forEach((s: any) => {
          if (s.dependencies) {
            s.dependencies.forEach((depId: string) => {
              edges.push({
                 id: `e_${depId}-${s.step_id || s.id}`,
                 source: depId,
                 target: s.step_id || s.id,
                 animated: true,
              });
            });
          }
        });
      }
    }

    // Prevent saving empty snapshots when canvas is empty and no workflow loaded
    if (nodes.length === 0) {
      throw new Error('Cannot save empty workflow snapshot. Canvas has 0 nodes.');
    }

    const mappedNodes = nodes.map((n: any) => ({
      id: n.id || n.step_id,
      type: n.type || 'customNode',
      step_id: n.id || n.step_id,
      provider: n.data?.provider || n.provider || 'Generic',
      operation_id: n.data?.operation_id || n.operation_id || 'generic.http.request',
      parameters: n.data?.parameters || n.parameters || {},
      data: n.data || { provider: n.provider, operation_id: n.operation_id, parameters: n.parameters },
      position: n.position || { x: 250, y: 100 },
    }));

    const mappedEdges = edges.map((e: any) => ({
      id: e.id || `e_${e.source}_${e.target}`,
      source: e.source,
      target: e.target,
    }));

    console.log(
      `[AI-26 DIAGNOSTIC][2. STORE SAVE_VERSION READY] mapped_nodes=${mappedNodes.length} mapped_edges=${mappedEdges.length}`
    );

    const spec = {
      workflow_id: workflowId,
      nodes: mappedNodes,
      edges: mappedEdges,
      steps: mappedNodes,
    };

    try {
      const res = await workflowApi.createVersion(workflowId, {
        name: name || `Version ${savedVersions.length + 1}`,
        workflow_spec: spec,
        commit_message: commitMessage,
      });

      const newVer: WorkflowVersion = {
        version_id: res.version_id,
        workflow_id: res.workflow_id,
        version_number: res.version_number,
        saved_at: new Date((res.created_at || Date.now() / 1000) * 1000).toISOString(),
        name: res.name || name || `Version ${res.version_number}`,
        nodes: res.nodes || mappedNodes,
        edges: res.edges || mappedEdges,
        node_count: res.node_count ?? mappedNodes.length,
        edge_count: res.edge_count ?? mappedEdges.length,
        commit_message: res.commit_message,
      };

      set({
        savedVersions: [newVer, ...savedVersions.filter((v) => v.version_id !== res.version_id)],
        currentVersionNumber: res.version_number,
        restoredNotice: null,
      });
    } catch (err: any) {
      if (err?.message?.includes('Cannot save empty workflow snapshot')) {
        throw err;
      }
      const fallbackVer: WorkflowVersion = {
        version_id: `v${savedVersions.length + 1}.0`,
        version_number: savedVersions.length + 1,
        saved_at: new Date().toISOString(),
        name: name || `Workflow Draft v${savedVersions.length + 1}`,
        nodes,
        edges,
        node_count: nodes.length,
        edge_count: edges.length,
      };
      set({ savedVersions: [fallbackVer, ...savedVersions] });
    }
  },

  restoreVersion: async (versionItem: any) => {
    const workflowId = versionItem.workflow_id || get().workflowId;
    try {
      const res = await workflowApi.restoreVersion(workflowId, versionItem.version_id || versionItem.version_number);
      const rawNodes = res.nodes || res.workflow_spec?.nodes || res.workflow_spec?.steps || versionItem.nodes || [];
      const rawEdges = res.edges || res.workflow_spec?.edges || versionItem.edges || [];

      const rfNodes: Node[] = rawNodes.map((n: any, idx: number) => {
        const nid = n.id || n.step_id || `step_${idx + 1}`;
        const provider = n.data?.provider || n.provider || 'Generic';
        const operation_id = n.data?.operation_id || n.operation_id || n.operation || 'generic.http.request';
        const parameters = n.data?.parameters || n.parameters || {};
        const label = n.data?.label || provider || nid;

        return {
          id: nid,
          type: n.type || 'customNode',
          position: n.position || { x: 250, y: 50 + idx * 160 },
          data: {
            ...(n.data || {}),
            label,
            provider,
            operation_id,
            parameters,
            step_id: nid,
          },
        };
      });

      const rfEdges: Edge[] = rawEdges.map((e: any) => ({
        id: e.id || `e_${e.source}_${e.target}`,
        source: e.source,
        target: e.target,
        animated: true,
      }));

      const MIN_NODE_VERTICAL_SPACING = 180;

      const hasInsufficientSpacing =
        rfNodes.length > 1 &&
        rfNodes.some((node, idx) => {
          if (idx === 0) return false;
          const previous = rfNodes[idx - 1];
          return (
            Math.abs(node.position.y - previous.position.y) < MIN_NODE_VERTICAL_SPACING ||
            (node.position.x === previous.position.x && node.position.y === previous.position.y)
          );
        });

      const layoutResult = hasInsufficientSpacing
        ? getAutoLayoutElements(rfNodes, rfEdges)
        : { nodes: rfNodes, edges: rfEdges };

      const verNum = res.version_number || versionItem.version_number || 1;
      get().pushHistory();
      set({
        nodes: layoutResult.nodes,
        edges: layoutResult.edges,
        currentVersionNumber: verNum,
        restoredNotice: `Version ${verNum} restored. Save to create a new version.`,
      });
    } catch {
      // Fallback local restore
      const verNum = versionItem.version_number || 1;
      const rawNodes = versionItem.nodes || versionItem.workflow_spec?.nodes || [];
      const rawEdges = versionItem.edges || versionItem.workflow_spec?.edges || [];

      const rfNodes: Node[] = rawNodes.map((n: any, idx: number) => {
        const nid = n.id || n.step_id || `step_${idx + 1}`;
        const provider = n.data?.provider || n.provider || 'Generic';
        const operation_id = n.data?.operation_id || n.operation_id || n.operation || 'generic.http.request';
        const parameters = n.data?.parameters || n.parameters || {};
        const label = n.data?.label || provider || nid;

        return {
          id: nid,
          type: n.type || 'customNode',
          position: n.position || { x: 250, y: 50 + idx * 160 },
          data: {
            ...(n.data || {}),
            label,
            provider,
            operation_id,
            parameters,
            step_id: nid,
          },
        };
      });

      const rfEdges: Edge[] = rawEdges.map((e: any) => ({
        id: e.id || `e_${e.source}_${e.target}`,
        source: e.source,
        target: e.target,
        animated: true,
      }));

      const MIN_NODE_VERTICAL_SPACING = 180;

      const hasInsufficientSpacing =
        rfNodes.length > 1 &&
        rfNodes.some((node, idx) => {
          if (idx === 0) return false;
          const previous = rfNodes[idx - 1];
          return (
            Math.abs(node.position.y - previous.position.y) < MIN_NODE_VERTICAL_SPACING ||
            (node.position.x === previous.position.x && node.position.y === previous.position.y)
          );
        });

      const layoutResult = hasInsufficientSpacing
        ? getAutoLayoutElements(rfNodes, rfEdges)
        : { nodes: rfNodes, edges: rfEdges };

      get().pushHistory();
      set({
        nodes: layoutResult.nodes,
        edges: layoutResult.edges,
        currentVersionNumber: verNum,
        restoredNotice: `Version ${verNum} restored. Save to create a new version.`,
      });
    }
  },

  loadWorkflowFromDefinition: (wf: any) => {
    if (!wf) return;
    const def = typeof wf.definition === 'string' ? JSON.parse(wf.definition) : (wf.definition || wf.workflow_spec || wf);
    // Canonical string workflow ID contract: prioritize definition.workflow_id over database UUID
    const canonicalId =
      def?.workflow_id ||
      wf.workflow_id ||
      (wf.id && !wf.id.includes('-') ? wf.id : undefined) ||
      get().workflowId ||
      'wf_studio_1';
    const databaseId = wf.id && wf.id.includes('-') ? wf.id : wf.id || null;
    const versionNum = wf.version || wf.version_number || 1;

    let rawNodes = def?.nodes || wf.nodes || def?.steps || wf.steps || [];
    let rawEdges = def?.edges || wf.edges || [];

    const rfNodes: Node[] = rawNodes.map((n: any, idx: number) => {
      const nid = n.id || n.step_id || `step_${idx + 1}`;
      const provider = n.data?.provider || n.provider || 'Generic';
      const operation_id = n.data?.operation_id || n.operation_id || n.operation || 'generic.http.request';
      const parameters = n.data?.parameters || n.parameters || {};
      const label = n.data?.label || n.name || n.title || provider || nid;

      return {
        id: nid,
        type: n.type || 'customNode',
        position: n.position && (n.position.x !== 0 || n.position.y !== 0) ? n.position : { x: 250, y: 50 + idx * 160 },
        data: {
          ...(n.data || {}),
          label,
          provider,
          operation_id,
          parameters,
          step_id: nid,
        },
      };
    });

    const rfEdges: Edge[] = rawEdges.map((e: any) => ({
      id: e.id || `e_${e.source}_${e.target}`,
      source: e.source,
      target: e.target,
      animated: true,
    }));

    const MIN_NODE_VERTICAL_SPACING = 180;
    const hasInsufficientSpacing =
      rfNodes.length > 1 &&
      rfNodes.some((node, idx) => {
        if (idx === 0) return false;
        const previous = rfNodes[idx - 1];
        return (
          Math.abs(node.position.y - previous.position.y) < MIN_NODE_VERTICAL_SPACING ||
          (node.position.x === previous.position.x && node.position.y === previous.position.y)
        );
      });

    const layoutResult = hasInsufficientSpacing
      ? getAutoLayoutElements(rfNodes, rfEdges)
      : { nodes: rfNodes, edges: rfEdges };

    set({
      workflowId: canonicalId,
      databaseWorkflowId: databaseId,
      currentVersionNumber: versionNum,
      nodes: layoutResult.nodes,
      edges: layoutResult.edges,
      selectedNode: null,
      restoredNotice: null,
    });
  },

  loadWorkflowFromBackend: async (id: string) => {
    if (!id) return;
    try {
      const data = await workflowApi.getWorkflowDetails(id);
      if (data) {
        const currentWfId = get().workflowId;
        const currentDbWfId = get().databaseWorkflowId;
        const currentNodes = get().nodes;

        // Guard against late/stale default studio responses:
        // If current canvas already has nodes for a specific active workflow, don't allow a late default studio response to overwrite it
        if (
          id === 'wf_studio_1' &&
          currentWfId !== 'wf_studio_1' &&
          currentNodes.length > 0
        ) {
          console.warn(`[Hydration Guard] Ignoring stale backend response for "${id}"; active workflow is "${currentWfId}" with ${currentNodes.length} nodes.`);
          return;
        }

        const rawNodes = data.definition?.nodes || (data as any).nodes || data.definition?.steps || (data as any).steps || [];
        if (rawNodes.length === 0 && currentNodes.length > 0 && (currentWfId === id || currentDbWfId === id)) {
          console.warn(`[Hydration Guard] Ignoring empty response for "${id}"; canvas already has ${currentNodes.length} nodes.`);
          return;
        }

        get().loadWorkflowFromDefinition(data);
      }
    } catch (e) {
      console.error('Failed to load workflow details from backend:', e);
    }
  },
}));
