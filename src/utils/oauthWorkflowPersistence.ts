import { useWorkflowStore } from '../store/useWorkflowStore';

export const OAUTH_WORKFLOW_SNAPSHOT_KEY = 'agentflow_pending_oauth_workflow';
export const SNAPSHOT_MAX_AGE_MS = 30 * 60 * 1000; // 30 minutes

export interface OAuthWorkflowSnapshot {
  workflowId: string;
  nodes: any[];
  edges: any[];
  generatedWorkflow?: any;
  prompt?: string;
  timestamp: number;
}

/**
 * Saves a snapshot of current workflow state to sessionStorage prior to OAuth redirect.
 */
export function saveWorkflowOAuthSnapshot(prompt?: string): void {
  try {
    const store = useWorkflowStore.getState();
    if (!store.nodes || store.nodes.length === 0) {
      console.log('[OAuthPersistence] No nodes to snapshot.');
      return;
    }

    const snapshot: OAuthWorkflowSnapshot = {
      workflowId: store.workflowId,
      nodes: store.nodes,
      edges: store.edges,
      generatedWorkflow: store.generatedWorkflow,
      prompt: prompt,
      timestamp: Date.now(),
    };

    sessionStorage.setItem(OAUTH_WORKFLOW_SNAPSHOT_KEY, JSON.stringify(snapshot));
    console.log(`[OAuthPersistence] Saved snapshot with ${snapshot.nodes.length} nodes and ${snapshot.edges.length} edges.`);
  } catch (err) {
    console.error('[OAuthPersistence] Failed to save snapshot:', err);
  }
}

/**
 * Restores pending workflow state from sessionStorage if valid and fresh (< 30 mins).
 * Returns true if snapshot was restored, false otherwise.
 */
export function restoreWorkflowOAuthSnapshot(): boolean {
  try {
    const raw = sessionStorage.getItem(OAUTH_WORKFLOW_SNAPSHOT_KEY);
    if (!raw) return false;

    const snapshot: OAuthWorkflowSnapshot = JSON.parse(raw);

    // Validate timestamp freshness (30 minutes)
    if (!snapshot.timestamp || Date.now() - snapshot.timestamp > SNAPSHOT_MAX_AGE_MS) {
      console.warn('[OAuthPersistence] Snapshot expired or missing timestamp. Removing.');
      sessionStorage.removeItem(OAUTH_WORKFLOW_SNAPSHOT_KEY);
      return false;
    }

    // Validate structure
    if (!Array.isArray(snapshot.nodes) || !Array.isArray(snapshot.edges)) {
      console.warn('[OAuthPersistence] Invalid snapshot structure. Removing.');
      sessionStorage.removeItem(OAUTH_WORKFLOW_SNAPSHOT_KEY);
      return false;
    }

    const store = useWorkflowStore.getState();
    if (snapshot.workflowId) {
      store.setWorkflowId(snapshot.workflowId);
    }

    store.setNodes(snapshot.nodes);
    store.setEdges(snapshot.edges);



    if (snapshot.generatedWorkflow) {
      store.setWorkflow(snapshot.generatedWorkflow);
    }

    store.setRestoredNotice('✓ Restored generated workflow after OAuth authentication.');

    sessionStorage.removeItem(OAUTH_WORKFLOW_SNAPSHOT_KEY);
    console.log(`[OAuthPersistence] Successfully restored snapshot with ${snapshot.nodes.length} nodes.`);
    return true;
  } catch (err) {
    console.error('[OAuthPersistence] Failed to restore snapshot:', err);
    try {
      sessionStorage.removeItem(OAUTH_WORKFLOW_SNAPSHOT_KEY);
    } catch {}
    return false;
  }
}

/**
 * Checks if a valid snapshot exists in sessionStorage.
 */
export function hasPendingOAuthWorkflowSnapshot(): boolean {
  try {
    const raw = sessionStorage.getItem(OAUTH_WORKFLOW_SNAPSHOT_KEY);
    if (!raw) return false;
    const snapshot: OAuthWorkflowSnapshot = JSON.parse(raw);
    if (!snapshot.timestamp || Date.now() - snapshot.timestamp > SNAPSHOT_MAX_AGE_MS) {
      return false;
    }
    return Array.isArray(snapshot.nodes) && snapshot.nodes.length > 0;
  } catch {
    return false;
  }
}

/**
 * Clears any pending snapshot.
 */
export function clearPendingOAuthWorkflowSnapshot(): void {
  try {
    sessionStorage.removeItem(OAUTH_WORKFLOW_SNAPSHOT_KEY);
  } catch {}
}
