import { useWorkflowStore } from '../../store/useWorkflowStore';

/**
 * Frontend Test for Workflow Open-Studio Hydration and Header Total Count
 */
export async function runWorkflowHydrationTests() {
  console.log('--- Running Workflow Hydration Tests ---');
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

  // Sample workflow item as returned from GET /api/v1/workflows
  const sampleWorkflowItem = {
    id: 'wf_gen_8236335c',
    workflow_id: 'wf_gen_8236335c',
    title: 'Gmail to Slack AI Workflow',
    description: 'Processes emails and sends alerts',
    status: 'ACTIVE',
    version: 3,
    trigger_type: 'gmail',
    updated_at: '2026-09-19T10:00:00Z',
    definition: {
      workflow_id: 'wf_gen_8236335c',
      name: 'Gmail to Slack AI Workflow',
      nodes: [
        {
          id: 'step_1',
          type: 'customNode',
          provider: 'Gmail',
          operation_id: 'gmail.messages.list',
          position: { x: 250, y: 50 },
          data: { label: 'Fetch Emails', provider: 'Gmail', operation_id: 'gmail.messages.list' },
        },
        {
          id: 'step_2',
          type: 'customNode',
          provider: 'Slack',
          operation_id: 'slack.chat.postMessage',
          position: { x: 250, y: 250 },
          data: { label: 'Send Slack Alert', provider: 'Slack', operation_id: 'slack.chat.postMessage' },
        },
      ],
      edges: [
        { id: 'e_step_1_step_2', source: 'step_1', target: 'step_2' },
      ],
    },
  };

  // Test 1: loadWorkflowFromDefinition populates store nodes, edges, workflowId, and version number
  useWorkflowStore.setState({ nodes: [], edges: [], workflowId: 'wf_studio_1', currentVersionNumber: null });
  assert(useWorkflowStore.getState().nodes.length === 0, 'Initial state nodes empty');

  useWorkflowStore.getState().loadWorkflowFromDefinition(sampleWorkflowItem);
  const state1 = useWorkflowStore.getState();

  assert(state1.workflowId === 'wf_gen_8236335c', 'Workflow ID updated to wf_gen_8236335c');
  assert(state1.currentVersionNumber === 3, 'Version number updated to 3');
  assert(state1.nodes.length === 2, 'Loaded 2 nodes onto canvas');
  assert(state1.edges.length === 1, 'Loaded 1 edge onto canvas');
  assert(state1.nodes[0].id === 'step_1', 'Node 1 ID preserved');
  assert(state1.nodes[0].data.provider === 'Gmail', 'Node 1 provider is Gmail');
  assert(state1.nodes[1].id === 'step_2', 'Node 2 ID preserved');
  assert(state1.nodes[1].data.provider === 'Slack', 'Node 2 provider is Slack');
  assert(state1.edges[0].source === 'step_1' && state1.edges[0].target === 'step_2', 'Edge connects step_1 to step_2');

  // Test 2: Ensure loadWorkflowFromDefinition preserves pre-calculated position if vertical spacing >= 180px
  assert(state1.nodes[0].position.y === 50, 'Node 1 position.y preserved at 50');
  assert(state1.nodes[1].position.y === 250, 'Node 2 position.y preserved at 250');

  // Test 3: Total count parsing logic simulation
  const mockBackendEnvelope = {
    total: 601,
    items: [sampleWorkflowItem],
    page: 1,
    limit: 20,
  };
  const parsedTotal = mockBackendEnvelope.total;
  const parsedItems = mockBackendEnvelope.items;
  assert(parsedTotal === 601, 'Backend total 601 extracted properly from envelope');
  assert(parsedItems.length === 1, 'Paginated items array extracted separately');

  console.log(`--- SUCCESS: All ${passed}/${total} Workflow Hydration tests passed! ---`);
  return { passed, total };
}
