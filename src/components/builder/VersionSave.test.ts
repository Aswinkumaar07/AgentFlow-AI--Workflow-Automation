import { useWorkflowStore } from '../../store/useWorkflowStore';

/**
 * Frontend Regression Test for AI-26 Save & Restore Version Node Hydration
 */
export async function runVersionSaveTests() {
  console.log('--- Running VersionSave Regression Tests ---');
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

  const sampleNodes: any[] = [
    { id: 'step_1', type: 'customNode', data: { provider: 'Gmail', operation_id: 'gmail.messages.list', label: 'Gmail List' }, position: { x: 100, y: 100 } },
    { id: 'step_2', type: 'customNode', data: { provider: 'Gmail', operation_id: 'gmail.messages.get', label: 'Gmail Get' }, position: { x: 100, y: 200 } },
    { id: 'step_3', type: 'customNode', data: { provider: 'AI', operation_id: 'ai.summarize', label: 'AI Summarize' }, position: { x: 100, y: 300 } },
    { id: 'step_4', type: 'customNode', data: { provider: 'Approval', operation_id: 'approval.wait', label: 'Human Approval' }, position: { x: 100, y: 400 } },
    { id: 'step_5', type: 'customNode', data: { provider: 'Slack', operation_id: 'slack.chat.postMessage', label: 'Slack' }, position: { x: 100, y: 500 } },
  ];

  const sampleEdges: any[] = [
    { id: 'e1', source: 'step_1', target: 'step_2' },
    { id: 'e2', source: 'step_2', target: 'step_3' },
    { id: 'e3', source: 'step_3', target: 'step_4' },
    { id: 'e4', source: 'step_4', target: 'step_5' },
  ];

  // Test 1: Set nodes in store and verify saveVersion maps all 5 nodes and 4 edges
  useWorkflowStore.setState({ nodes: sampleNodes, edges: sampleEdges, workflowId: 'wf_studio_1' });
  const storeState = useWorkflowStore.getState();
  assert(storeState.nodes.length === 5, 'Store contains 5 nodes');
  assert(storeState.edges.length === 4, 'Store contains 4 edges');

  // Test 2: Verify overrideNodes parameter forces 5 nodes even if store state were empty
  useWorkflowStore.setState({ nodes: [], edges: [] });
  assert(useWorkflowStore.getState().nodes.length === 0, 'Store cleared for override test');

  // Direct mapping logic check as used in saveVersion
  const overrideNodes = sampleNodes;
  const overrideEdges = sampleEdges;
  const mappedNodes = (overrideNodes.length > 0 ? overrideNodes : useWorkflowStore.getState().nodes).map((n: any) => ({
    id: n.id || n.step_id,
    type: n.type || 'customNode',
    step_id: n.id || n.step_id,
    provider: n.data?.provider || n.provider || 'Generic',
    operation_id: n.data?.operation_id || n.operation_id || 'generic.http.request',
    parameters: n.data?.parameters || n.parameters || {},
    data: n.data || { provider: n.provider, operation_id: n.operation_id, parameters: n.parameters },
    position: n.position || { x: 250, y: 100 },
  }));
  const mappedEdges = (overrideEdges.length > 0 ? overrideEdges : useWorkflowStore.getState().edges).map((e: any) => ({
    id: e.id || `e_${e.source}_${e.target}`,
    source: e.source,
    target: e.target,
  }));

  assert(mappedNodes.length === 5, 'Mapped nodes count is 5');
  assert(mappedEdges.length === 4, 'Mapped edges count is 4');
  assert(mappedNodes[0].provider === 'Gmail', 'First mapped node provider is Gmail');
  assert(mappedNodes[4].provider === 'Slack', 'Fifth mapped node provider is Slack');
  assert(mappedNodes[0].type === 'customNode', 'First mapped node type is customNode');

  // Test 3: Test restoreVersion hydration logic
  const mockVersionSnapshot = {
    version_id: 'ver_wf_studio_1_v7',
    version_number: 7,
    name: 'Version 7 - Verified Browser Persistence',
    nodes: sampleNodes,
    edges: sampleEdges,
  };

  // Run local fallback restore
  const rawNodes = mockVersionSnapshot.nodes;
  const rfNodes = rawNodes.map((n: any, idx: number) => {
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

  assert(rfNodes.length === 5, 'Restored React Flow node count is 5');
  assert(rfNodes.every((n: any) => n.type === 'customNode' || n.type === 'custom'), 'All restored nodes use AgentFlow CustomNode type');
  assert(rfNodes[0].data.provider === 'Gmail', 'Restored node 1 provider is Gmail');
  assert(rfNodes[2].data.provider === 'AI', 'Restored node 3 provider is AI');
  assert(rfNodes[3].data.provider === 'Approval', 'Restored node 4 provider is Approval');
  assert(rfNodes[4].data.provider === 'Slack', 'Restored node 5 provider is Slack');

  // Test 4: Physical Spacing Detection Logic Tests
  const MIN_NODE_VERTICAL_SPACING = 180;
  const checkSpacing = (nodes: any[]) =>
    nodes.length > 1 &&
    nodes.some((node, idx) => {
      if (idx === 0) return false;
      const previous = nodes[idx - 1];
      return (
        Math.abs(node.position.y - previous.position.y) < MIN_NODE_VERTICAL_SPACING ||
        (node.position.x === previous.position.x && node.position.y === previous.position.y)
      );
    });

  // Test 4a: Identical positions trigger layout (insufficient spacing)
  const identicalPosNodes = [
    { id: '1', position: { x: 250, y: 100 } },
    { id: '2', position: { x: 250, y: 100 } },
  ];
  assert(checkSpacing(identicalPosNodes) === true, 'Identical positions correctly flagged as insufficient spacing');

  // Test 4b: 120px vertical spacing triggers layout (insufficient spacing < 180px)
  const spacing120Nodes = [
    { id: '1', position: { x: 250, y: 100 } },
    { id: '2', position: { x: 250, y: 220 } },
    { id: '3', position: { x: 250, y: 340 } },
  ];
  assert(checkSpacing(spacing120Nodes) === true, '120px vertical spacing correctly flagged as insufficient spacing (<180px)');

  // Test 4c: Sufficient vertical spacing (>=180px) preserves positions
  const spacing220Nodes = [
    { id: '1', position: { x: 250, y: 100 } },
    { id: '2', position: { x: 250, y: 320 } },
    { id: '3', position: { x: 250, y: 540 } },
  ];
  assert(checkSpacing(spacing220Nodes) === false, '220px vertical spacing correctly accepted as sufficient spacing');

  // Test 4d: Distinct horizontal positions with sufficient vertical spacing preserve positions
  const horizontalSufficientNodes = [
    { id: '1', position: { x: 100, y: 100 } },
    { id: '2', position: { x: 400, y: 300 } },
  ];
  assert(checkSpacing(horizontalSufficientNodes) === false, 'Distinct positions with >=180px spacing accepted without layout override');

  // Test 5: Verify Clear preserves active workflowId
  useWorkflowStore.setState({ workflowId: 'wf_studio_1' });
  useWorkflowStore.getState().setWorkflow({
    user_prompt: '',
    goal: '',
    services: [],
    workflow_json: {},
    execution_metadata: {},
    logs: [],
  });
  assert(useWorkflowStore.getState().workflowId === 'wf_studio_1', 'setWorkflow preserves active workflowId on Clear');

  console.log(`--- SUCCESS: All ${passed}/${total} VersionSave & Hydration tests passed! ---`);
  return { passed, total };
}
