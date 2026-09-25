import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  useReactFlow,
  ReactFlowProvider,
  applyNodeChanges,
  applyEdgeChanges,
  reconnectEdge,
  MarkerType,
} from '@xyflow/react';
import type { Connection, Edge, Node, NodeChange, EdgeChange } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CustomNode } from './CustomNode';
import { NodeContextMenu } from './NodeContextMenu';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import { getAutoLayoutElements } from '../../utils/layout';
import { useBuilderKeyboard } from '../../hooks/useBuilderKeyboard';

// Defined outside component — stable reference, no re-renders
const nodeTypes = {
  customNode: CustomNode,
  custom: CustomNode,
};

interface ContextMenuState {
  x: number;
  y: number;
  nodeId: string;
  nodeLabel: string;
}

interface WorkflowCanvasProps {
  readOnly?: boolean;
  onViewportChange?: (viewport: { x: number; y: number; zoom: number }) => void;
}

const WorkflowCanvasInner: React.FC<WorkflowCanvasProps> = ({ readOnly = false, onViewportChange }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const edgeReconnectSuccessful = useRef(true);
  const { screenToFlowPosition } = useReactFlow();

  const {
    nodes: storeNodes,
    edges: storeEdges,
    setNodes: setStoreNodes,
    setEdges: setStoreEdges,
    generatedWorkflow,
    setSelectedNode,
    setSelectedEdgeIds,
    addNode,
    duplicateNode,
    deleteSelected,
    copySelectedNodes,
  } = useWorkflowStore();

  const [nodes, setNodes] = useNodesState<Node>(storeNodes);
  const [edges, setEdges] = useEdgesState<Edge>(storeEdges);
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);

  // ──────────────────────────────────────────────────────────────
  // FIX: Sync LOCAL changes (drag, resize) back to Zustand store safely
  // ──────────────────────────────────────────────────────────────
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setStoreNodes((currentStoreNodes) => {
        const baseNodes = currentStoreNodes.length > 0 ? currentStoreNodes : nodes;
        if (baseNodes.length === 0 && !changes.some((c) => c.type === 'add')) {
          return currentStoreNodes;
        }
        const updated = applyNodeChanges(changes, baseNodes);
        setNodes(updated as Node[]);
        return updated as Node[];
      });
    },
    [nodes, setNodes, setStoreNodes]
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      setStoreEdges((currentStoreEdges) => {
        const baseEdges = currentStoreEdges.length > 0 ? currentStoreEdges : edges;
        if (baseEdges.length === 0 && !changes.some((c) => c.type === 'add')) {
          return currentStoreEdges;
        }
        const updated = applyEdgeChanges(changes, baseEdges);
        setEdges(updated as Edge[]);

        // Track selected edge IDs
        const selectedIds = (updated as Edge[])
          .filter((e) => e.selected)
          .map((e) => e.id);
        setSelectedEdgeIds(selectedIds);
        return updated as Edge[];
      });
    },
    [edges, setEdges, setStoreEdges, setSelectedEdgeIds]
  );

  // ──────────────────────────────────────────────────────────────
  // Sync store ↔ canvas bidirectionally
  // ──────────────────────────────────────────────────────────────
  useEffect(() => {
    setNodes(storeNodes);
  }, [storeNodes, setNodes]);

  useEffect(() => {
    setEdges(storeEdges);
  }, [storeEdges, setEdges]);


  // ──────────────────────────────────────────────────────────────
  // AI-generated workflow DAG → canvas
  // ──────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!generatedWorkflow) return;

    let newNodes: Node[] = [];
    let newEdges: Edge[] = [];

    const wfJson = generatedWorkflow.workflow_json;

    if (wfJson && wfJson.nodes && Array.isArray(wfJson.nodes) && wfJson.nodes.length > 0) {
      newNodes = wfJson.nodes.map((n: any, idx: number) => ({
        id: n.id || `step_${idx + 1}`,
        type: 'customNode',
        position: n.position || { x: 250, y: idx * 160 + 50 },
        data: n.data || {
          label: n.label || n.provider || n.id,
          provider: n.provider || 'Generic',
          operation_id: n.operation_id || 'generic.http.request',
          parameters: n.parameters || {},
          step_id: n.id || `step_${idx + 1}`,
        },
      }));

      if (wfJson.edges && Array.isArray(wfJson.edges)) {
        newEdges = wfJson.edges.map((e: any) => ({
          id: e.id || `e_${e.source}_${e.target}`,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed, color: '#FF6D00' },
          style: { stroke: '#FF6D00', strokeWidth: 2 },
        }));
      }
    } else if (generatedWorkflow.steps && Array.isArray(generatedWorkflow.steps)) {
      newNodes = generatedWorkflow.steps.map((step: any, idx: number) => ({
        id: step.step_id,
        type: 'customNode',
        position: { x: 250, y: idx * 160 + 50 },
        data: {
          label: step.provider,
          provider: step.provider,
          operation_id: step.operation_id,
          parameters: step.parameters,
          step_id: step.step_id,
        },
      }));

      generatedWorkflow.steps.forEach((step: any) => {
        if (step.dependencies) {
          step.dependencies.forEach((depId: string) => {
            newEdges.push({
              id: `e_${depId}-${step.step_id}`,
              source: depId,
              target: step.step_id,
              animated: true,
              markerEnd: { type: MarkerType.ArrowClosed, color: '#6366F1' },
              style: { stroke: '#6366F1', strokeWidth: 2 },
            });
          });
        }
      });
    }

    if (newNodes.length > 0) {
      const { nodes: layoutedNodes, edges: layoutedEdges } = getAutoLayoutElements(newNodes, newEdges);
      console.log('[Tracing] Workflow Rendered:', layoutedNodes.map((n) => n.data?.label || n.data?.provider || n.id));
      setStoreNodes(layoutedNodes);
      setStoreEdges(layoutedEdges);
    }
  }, [generatedWorkflow, setStoreNodes, setStoreEdges]);

  // ──────────────────────────────────────────────────────────────
  // Keyboard shortcuts
  // ──────────────────────────────────────────────────────────────
  const getSelectedNodeIds = useCallback(
    () => nodes.filter((n) => n.selected).map((n) => n.id),
    [nodes]
  );
  const getSelectedEdgeIds = useCallback(
    () => edges.filter((e) => e.selected).map((e) => e.id),
    [edges]
  );

  useBuilderKeyboard(getSelectedNodeIds, getSelectedEdgeIds);

  // ──────────────────────────────────────────────────────────────
  // Connect / Reconnect edges
  // ──────────────────────────────────────────────────────────────
  const onConnect = useCallback(
    (params: Connection) => {
      const updatedEdges = addEdge(
        {
          ...params,
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed, color: '#FF6D00' },
          style: { stroke: '#FF6D00', strokeWidth: 2 },
        },
        edges
      );
      setEdges(updatedEdges);
      setStoreEdges(updatedEdges);
    },
    [edges, setEdges, setStoreEdges]
  );

  const onReconnectStart = useCallback(() => {
    edgeReconnectSuccessful.current = false;
  }, []);

  const onReconnect = useCallback(
    (oldEdge: Edge, newConnection: Connection) => {
      edgeReconnectSuccessful.current = true;
      const updatedEdges = reconnectEdge(oldEdge, newConnection, edges);
      setEdges(updatedEdges);
      setStoreEdges(updatedEdges);
    },
    [edges, setEdges, setStoreEdges]
  );

  const onReconnectEnd = useCallback(
    (_: MouseEvent | TouchEvent, edge: Edge) => {
      if (!edgeReconnectSuccessful.current) {
        // Drop onto canvas without valid target → remove edge
        const filtered = edges.filter((e) => e.id !== edge.id);
        setEdges(filtered);
        setStoreEdges(filtered);
      }
      edgeReconnectSuccessful.current = true;
    },
    [edges, setEdges, setStoreEdges]
  );

  // ──────────────────────────────────────────────────────────────
  // Node interactions
  // ──────────────────────────────────────────────────────────────
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(node);
      setContextMenu(null);
    },
    [setSelectedNode]
  );

  const onNodeContextMenu = useCallback(
    (e: React.MouseEvent, node: Node) => {
      e.preventDefault();
      setSelectedNode(node);
      setContextMenu({
        x: e.clientX,
        y: e.clientY,
        nodeId: node.id,
        nodeLabel: String((node.data as any)?.label || node.id),
      });
    },
    [setSelectedNode]
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setContextMenu(null);
  }, [setSelectedNode]);

  // ──────────────────────────────────────────────────────────────
  // Drag & Drop from palette
  // ──────────────────────────────────────────────────────────────
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const rawData = event.dataTransfer.getData('application/reactflow');
      if (!rawData) return;

      const item = JSON.parse(rawData);
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNodeId = `step_${Math.random().toString(36).substring(2, 7)}`;
      const newNode: Node = {
        id: newNodeId,
        type: 'customNode',
        position,
        data: {
          label: item.name,
          provider: item.name,
          operation_id: item.operation_id,
          parameters: item.defaultParams || {},
          step_id: newNodeId,
        },
      };

      addNode(newNode);
    },
    [screenToFlowPosition, addNode]
  );

  // Context menu actions
  const ctxNodeId = contextMenu?.nodeId;

  const handleCtxDuplicate = useCallback(() => {
    if (ctxNodeId) duplicateNode(ctxNodeId);
  }, [ctxNodeId, duplicateNode]);

  const handleCtxDelete = useCallback(() => {
    if (ctxNodeId) deleteSelected([ctxNodeId], []);
  }, [ctxNodeId, deleteSelected]);

  const handleCtxCopy = useCallback(() => {
    if (ctxNodeId) copySelectedNodes([ctxNodeId]);
  }, [ctxNodeId, copySelectedNodes]);

  const handleCtxRename = useCallback(() => {
    // Trigger inline rename: select the node and let CustomNode handle it via double-click simulation
    if (ctxNodeId) {
      const nodeEl = document.querySelector(`[data-id="${ctxNodeId}"] span[title="Double-click to rename"]`) as HTMLElement;
      nodeEl?.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
    }
  }, [ctxNodeId]);

  const handleCtxInspect = useCallback(() => {
    if (ctxNodeId) {
      const node = nodes.find((n) => n.id === ctxNodeId);
      if (node) setSelectedNode(node);
    }
  }, [ctxNodeId, nodes, setSelectedNode]);

  return (
    <div
      ref={reactFlowWrapper}
      className="w-full h-full relative bg-[#0E0918] border border-[rgba(255,255,255,0.12)] rounded-2xl overflow-hidden shadow-2xl"
      style={{ width: '100%', height: '100%', minHeight: '400px' }}
      onContextMenu={(e) => e.preventDefault()}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={readOnly ? undefined : onNodesChange}
        onEdgesChange={readOnly ? undefined : onEdgesChange}
        onConnect={readOnly ? undefined : onConnect}
        onReconnectStart={readOnly ? undefined : onReconnectStart}
        onReconnect={readOnly ? undefined : onReconnect}
        onReconnectEnd={readOnly ? undefined : onReconnectEnd}
        onNodeClick={readOnly ? undefined : onNodeClick}
        onNodeContextMenu={readOnly ? undefined : onNodeContextMenu}
        onPaneClick={readOnly ? undefined : onPaneClick}
        onDragOver={readOnly ? undefined : onDragOver}
        onDrop={readOnly ? undefined : onDrop}
        onMove={onViewportChange ? (_evt, vp) => onViewportChange(vp) : undefined}
        nodesDraggable={!readOnly}
        nodesConnectable={!readOnly}
        elementsSelectable={!readOnly}
        deleteKeyCode={readOnly ? null : ['Backspace', 'Delete']}
        multiSelectionKeyCode={readOnly ? null : 'Shift'}
        selectionKeyCode={readOnly ? null : 'Shift'}
        reconnectRadius={10}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Controls className="!bg-[#13102A]/90 !border-[rgba(255,255,255,0.12)] !text-white shadow-xl rounded-xl" />
        <MiniMap
          className="!bg-[#13102A]/90 !border-[rgba(255,255,255,0.12)] rounded-xl"
          nodeColor={(n) => {
            const p = (n.data as any)?.provider || '';
            if (p === 'Gmail') return '#f87171';
            if (p === 'Slack') return '#34d399';
            if (p === 'GitHub') return '#a78bfa';
            if (p === 'Condition' || p === 'IF' || p === 'Switch') return '#fbbf24';
            return '#FF6D00';
          }}
          maskColor="rgba(14,9,24,0.75)"
        />
        <Background gap={18} size={1} color="rgba(255,109,0,0.15)" />
      </ReactFlow>

      {contextMenu && (
        <NodeContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          nodeId={contextMenu.nodeId}
          nodeLabel={contextMenu.nodeLabel}
          onDuplicate={handleCtxDuplicate}
          onDelete={handleCtxDelete}
          onCopy={handleCtxCopy}
          onRename={handleCtxRename}
          onInspect={handleCtxInspect}
          onClose={() => setContextMenu(null)}
        />
      )}
    </div>
  );
};

export const WorkflowCanvas: React.FC<WorkflowCanvasProps> = (props) => (
  <ReactFlowProvider>
    <WorkflowCanvasInner {...props} />
  </ReactFlowProvider>
);
