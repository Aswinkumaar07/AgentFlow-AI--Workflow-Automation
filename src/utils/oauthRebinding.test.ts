import { rebindNodesWithOAuthConnections } from './oauthReadiness';
import type { OAuthConnection } from '../types/oauth';

export function runOAuthRebindingTests() {
  console.log('--- Running OAuth Re-binding Unit Tests (Requirements A - F) ---');
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

  // Sample nodes
  const gmailListNode = {
    id: 'step_1',
    type: 'customNode',
    data: {
      label: 'Gmail List',
      provider: 'Gmail',
      operation_id: 'gmail.messages.list',
      step_id: 'step_1',
      parameters: {
        max_results: 10,
        query: 'is:unread',
        credential_id: null,
        auth_status: 'unbound',
        auth_account_label: null,
      },
    },
  };

  const gmailGetNode = {
    id: 'step_2',
    type: 'customNode',
    data: {
      label: 'Gmail Get',
      provider: 'Gmail',
      operation_id: 'gmail.messages.get',
      step_id: 'step_2',
      parameters: {
        message_id: '{{step_1.messages[0].id}}',
        credential_id: null,
        auth_status: 'unbound',
        auth_account_label: null,
      },
    },
  };

  const aiNode = {
    id: 'step_3',
    type: 'customNode',
    data: {
      label: 'AI Summarize',
      provider: 'AI',
      operation_id: 'ai.summarize',
      step_id: 'step_3',
      parameters: {
        text: '{{step_2.snippet}}',
      },
    },
  };

  const realGoogleConn: OAuthConnection = {
    id: 'conn_google_094daab175',
    user_id: 'usr_1',
    provider: 'Google',
    status: 'CONNECTED',
    scopes: ['gmail.readonly'],
    created_at: Date.now(),
    account_label: 'aswinkumaar07@gmail.com',
  };

  // Test A: Restored Gmail node + real connected Gmail account -> correctly rebound
  const testA_nodes = [JSON.parse(JSON.stringify(gmailListNode))];
  const testA_result = rebindNodesWithOAuthConnections(testA_nodes, [realGoogleConn]);
  assert(testA_result[0].data.parameters.credential_id === 'conn_google_094daab175', 'Test A: credential_id rebound to conn_google_094daab175');
  assert(testA_result[0].data.parameters.auth_status === 'active', 'Test A: auth_status set to active');
  assert(testA_result[0].data.parameters.auth_account_label === 'aswinkumaar07@gmail.com', 'Test A: auth_account_label set to aswinkumaar07@gmail.com');

  // Test B: Restored Gmail node + no connection -> remains unbound
  const testB_nodes = [JSON.parse(JSON.stringify(gmailListNode))];
  const testB_result = rebindNodesWithOAuthConnections(testB_nodes, []);
  assert(testB_result[0].data.parameters.credential_id === null, 'Test B: credential_id remains null');
  assert(testB_result[0].data.parameters.auth_status === 'unbound', 'Test B: auth_status remains unbound');
  assert(testB_result[0].data.parameters.auth_account_label === null, 'Test B: auth_account_label remains null');

  // Test C: Stale AccountPicker entry (not in connections list) cannot cause binding
  const testC_nodes = [JSON.parse(JSON.stringify(gmailListNode))];
  const disconnectedConn: OAuthConnection = {
    id: 'conn_stale_123',
    user_id: 'usr_1',
    provider: 'Google',
    status: 'DISCONNECTED',
    scopes: [],
    created_at: Date.now(),
    account_label: 'stale@gmail.com',
  };
  const testC_result = rebindNodesWithOAuthConnections(testC_nodes, [disconnectedConn]);
  assert(testC_result[0].data.parameters.credential_id === null, 'Test C: Stale/disconnected connection cannot cause binding (credential_id null)');
  assert(testC_result[0].data.parameters.auth_status === 'unbound', 'Test C: auth_status remains unbound');

  // Test D: AI / internal node is never OAuth-bound
  const testD_nodes = [JSON.parse(JSON.stringify(aiNode))];
  const testD_result = rebindNodesWithOAuthConnections(testD_nodes, [realGoogleConn]);
  assert(testD_result[0].data.parameters.credential_id === undefined, 'Test D: AI node credential_id remains undefined');
  assert(testD_result[0].data.parameters.auth_status === undefined, 'Test D: AI node auth_status remains undefined');
  assert(JSON.stringify(testD_result[0]) === JSON.stringify(aiNode), 'Test D: AI node object structure completely unchanged');

  // Test E: Existing node parameters other than auth fields remain unchanged
  const testE_nodes = [JSON.parse(JSON.stringify(gmailListNode))];
  const testE_result = rebindNodesWithOAuthConnections(testE_nodes, [realGoogleConn]);
  assert(testE_result[0].data.parameters.max_results === 10, 'Test E: max_results remains 10');
  assert(testE_result[0].data.parameters.query === 'is:unread', 'Test E: query remains is:unread');

  // Test F: Multiple Gmail nodes bind consistently to the same valid active connection
  const testF_nodes = [JSON.parse(JSON.stringify(gmailListNode)), JSON.parse(JSON.stringify(gmailGetNode))];
  const testF_result = rebindNodesWithOAuthConnections(testF_nodes, [realGoogleConn]);
  assert(testF_result[0].data.parameters.credential_id === 'conn_google_094daab175', 'Test F: Node 1 credential_id rebound');
  assert(testF_result[1].data.parameters.credential_id === 'conn_google_094daab175', 'Test F: Node 2 credential_id rebound');
  assert(testF_result[0].data.parameters.auth_status === 'active', 'Test F: Node 1 auth_status active');
  assert(testF_result[1].data.parameters.auth_status === 'active', 'Test F: Node 2 auth_status active');

  console.log(`--- SUCCESS: All ${passed}/${total} OAuth re-binding unit tests passed! ---`);
  return { passed, total };
}

runOAuthRebindingTests();
