import { templatesApi } from '../../api/templates';
import { useWorkflowStore } from '../../store/useWorkflowStore';

/**
 * Frontend Test Suite for AI-32 Intelligent Workflow Template System
 */
export async function runTemplatesTests() {
  console.log('--- Running Templates System Tests ---');
  let passed = 0;
  let total = 0;

  function assert(condition: boolean, description: string) {
    total++;
    if (!condition) {
      console.error(`[FAIL] Test #${total}: ${description}`);
      throw new Error(`Test failed: ${description}`);
    } else {
      console.log(`[PASS] Test #${total}: ${description}`);
      passed++;
    }
  }

  // Test 1: Fetch templates catalog
  const templates = await templatesApi.getTemplates();
  assert(Array.isArray(templates), 'getTemplates returns an array');

  // Test 2: Instantiate template API structure
  const result = await templatesApi.instantiateTemplate('tpl_email_summarizer', {
    email_query: 'is:unread',
    max_emails: 5,
  });

  assert(result !== null && typeof result === 'object', 'instantiateTemplate returns a valid result object');
  assert(Boolean(result.workflow_id), 'Result contains workflow_id');
  assert(Boolean(result.version_number), 'Result contains version_number');
  assert(Array.isArray(result.nodes) && result.nodes.length === 2, 'Result contains 2 nodes');
  assert(Array.isArray(result.edges) && result.edges.length === 1, 'Result contains 1 edge');

  // Test 3: Populate Zustand workflow store and verify nodes are layouted and set
  useWorkflowStore.getState().setWorkflowId(result.workflow_id);
  useWorkflowStore.getState().setWorkflow({
    workflow_id: result.workflow_id,
    name: result.name,
    workflow_json: result.workflow_json,
    nodes: result.nodes,
    edges: result.edges,
  } as any);

  const store = useWorkflowStore.getState();
  assert(store.workflowId === result.workflow_id, 'useWorkflowStore updated with instantiated workflow_id');
  assert(store.nodes.length === 2, 'useWorkflowStore updated with 2 nodes');
  assert(store.edges.length === 1, 'useWorkflowStore updated with 1 edge');
  assert(store.nodes[0].type === 'customNode', 'Instantiated nodes use AgentFlow customNode UI type');

  // Test 4: Verify NO automatic execution was triggered
  const isGenerating = store.isGenerating;
  assert(!isGenerating, 'Workflow creation did NOT start automatic execution or generation spinner');

  console.log(`--- SUCCESS: All ${passed}/${total} Templates System tests passed! ---`);
  return { passed, total };
}
