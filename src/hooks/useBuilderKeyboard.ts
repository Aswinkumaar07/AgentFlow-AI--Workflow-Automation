import { useEffect } from 'react';
import { useWorkflowStore } from '../store/useWorkflowStore';

/**
 * Global keyboard shortcuts for the Workflow Builder.
 * Attach once at the WorkflowCanvas level.
 * Uses getState() inside the event listener so it always reads fresh store values.
 */
export const useBuilderKeyboard = (
  getSelectedNodeIds: () => string[],
  getSelectedEdgeIds: () => string[]
) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't fire shortcuts when typing in an input/textarea/select
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

      const ctrl = e.ctrlKey || e.metaKey;

      // Undo — Ctrl+Z
      if (ctrl && !e.shiftKey && e.key === 'z') {
        e.preventDefault();
        useWorkflowStore.getState().undo();
        return;
      }

      // Redo — Ctrl+Y or Ctrl+Shift+Z
      if (ctrl && (e.key === 'y' || (e.shiftKey && e.key === 'z'))) {
        e.preventDefault();
        useWorkflowStore.getState().redo();
        return;
      }

      // Select All — Ctrl+A
      if (ctrl && e.key === 'a') {
        e.preventDefault();
        useWorkflowStore.getState().setNodes(
          useWorkflowStore.getState().nodes.map((n) => ({ ...n, selected: true }))
        );
        return;
      }

      // Copy — Ctrl+C
      if (ctrl && e.key === 'c') {
        const ids = getSelectedNodeIds();
        if (ids.length > 0) {
          e.preventDefault();
          useWorkflowStore.getState().copySelectedNodes(ids);
        }
        return;
      }

      // Paste — Ctrl+V
      if (ctrl && e.key === 'v') {
        e.preventDefault();
        useWorkflowStore.getState().pasteNodes();
        return;
      }

      // Duplicate — Ctrl+D
      if (ctrl && e.key === 'd') {
        e.preventDefault();
        const ids = getSelectedNodeIds();
        ids.forEach((id) => useWorkflowStore.getState().duplicateNode(id));
        return;
      }

      // Delete / Backspace — remove selected nodes and edges
      if (e.key === 'Delete' || e.key === 'Backspace') {
        const nIds = getSelectedNodeIds();
        const eIds = getSelectedEdgeIds();
        if (nIds.length > 0 || eIds.length > 0) {
          e.preventDefault();
          useWorkflowStore.getState().deleteSelected(nIds, eIds);
        }
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
};
