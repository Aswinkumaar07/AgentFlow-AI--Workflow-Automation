import {
  checkNodeReadiness,
  isDynamicOpenAPIOperation,
  isDynamicPublicOpenAPIOperation,
  rebindNodesWithOAuthConnections,
} from './oauthReadiness';
import type { OAuthConnection } from '../types/oauth';

export function runOAuthReadinessPhase39Tests() {
  console.log('--- Running AI-37 Phase 39 Focused Execution-Readiness Tests (Scenarios A - E) ---');
  let passed = 0;
  let total = 0;

  function assert(condition: boolean, description: string) {
    total++;
    if (!condition) {
      console.error(`[FAIL] Phase 39 Test #${total}: ${description}`);
      throw new Error(`Test failed: ${description}`);
    } else {
      console.log(`[PASS] Phase 39 Test #${total}: ${description}`);
      passed++;
    }
  }

  const dummyConnections: OAuthConnection[] = [];

  const gmailConnection: OAuthConnection = {
    id: 'conn_gmail_123',
    user_id: 'usr_1',
    provider: 'Gmail',
    status: 'CONNECTED',
    scopes: ['gmail.readonly'],
    created_at: Date.now(),
  };

  // Scenario A: Native Gmail without OAuth -> BLOCKED
  const gmailNode = {
    id: 'step_gmail',
    data: {
      provider: 'Gmail',
      operation_id: 'gmail.messages.list',
    },
  };
  const resA = checkNodeReadiness([gmailNode], dummyConnections);
  assert(resA.ready === false, 'Scenario A: Un-connected native Gmail is BLOCKED');
  assert(resA.missing_connections.includes('Gmail'), 'Scenario A: missing_connections contains Gmail');

  // Scenario B: Native Slack without OAuth -> BLOCKED
  const slackNode = {
    id: 'step_slack',
    data: {
      provider: 'Slack',
      operation_id: 'slack.chat.postMessage',
    },
  };
  const resB = checkNodeReadiness([slackNode], dummyConnections);
  assert(resB.ready === false, 'Scenario B: Un-connected native Slack is BLOCKED');
  assert(resB.missing_connections.includes('Slack'), 'Scenario B: missing_connections contains Slack');

  // Scenario C: Dynamic public OpenAPI (Petstore getOrderById/getPetById) -> NOT BLOCKED
  const dynamicPublicPetstoreNode = {
    id: 'step_petstore_public',
    data: {
      provider: 'generic_rest',
      operation_id: 'getPetById',
      is_dynamic_api: true,
      security_schemes: {},
      security_requirements: [],
      parameters: {
        is_dynamic_api: true,
        security_schemes: {},
        security_requirements: [],
        petId: '{{step_1.data.petId}}',
      },
    },
  };
  assert(isDynamicOpenAPIOperation(dynamicPublicPetstoreNode) === true, 'Scenario C: Recognized as dynamic OpenAPI operation');
  assert(isDynamicPublicOpenAPIOperation(dynamicPublicPetstoreNode) === true, 'Scenario C: Recognized as public dynamic OpenAPI operation');
  const resC = checkNodeReadiness([dynamicPublicPetstoreNode], dummyConnections);
  assert(resC.ready === true, 'Scenario C: Dynamic public OpenAPI is NOT blocked by native OAuth preflight');
  assert(resC.missing_connections.length === 0, 'Scenario C: missing_connections is empty');

  // Scenario D: Dynamic authenticated OpenAPI (API Key / Bearer) -> NOT misclassified as native OAuth store requirement
  const dynamicAuthOpenAPINode = {
    id: 'step_auth_api',
    data: {
      provider: 'generic_rest',
      operation_id: 'getSecureData',
      is_dynamic_api: true,
      security_schemes: { apiKeyHeader: { type: 'apiKey', name: 'X-API-KEY', in: 'header' } },
      security_requirements: [{ apiKeyHeader: [] }],
      parameters: {
        is_dynamic_api: true,
        security_schemes: { apiKeyHeader: { type: 'apiKey', name: 'X-API-KEY', in: 'header' } },
        security_requirements: [{ apiKeyHeader: [] }],
      },
    },
  };
  assert(isDynamicOpenAPIOperation(dynamicAuthOpenAPINode) === true, 'Scenario D: Recognized as dynamic OpenAPI operation');
  assert(isDynamicPublicOpenAPIOperation(dynamicAuthOpenAPINode) === false, 'Scenario D: Recognized as non-public dynamic OpenAPI operation');
  const resD = checkNodeReadiness([dynamicAuthOpenAPINode], dummyConnections);
  assert(resD.ready === true, 'Scenario D: Dynamic authenticated OpenAPI is NOT misclassified as native OAuth store requirement');
  assert(resD.missing_connections.length === 0, 'Scenario D: missing_connections does NOT require generic_rest in OAuth store');

  // Scenario E: Existing generic/native behavior preserved
  const aiNode = { id: 'step_ai', data: { provider: 'AI', operation_id: 'ai.summarize' } };
  const resE_internal = checkNodeReadiness([aiNode], dummyConnections);
  assert(resE_internal.ready === true, 'Scenario E: Internal AI node is READY');

  const resE_gmail_connected = checkNodeReadiness([gmailNode], [gmailConnection]);
  assert(resE_gmail_connected.ready === true, 'Scenario E: Connected native Gmail node is READY');

  // Re-binding check: Dynamic OpenAPI nodes are never rebound to native OAuth connections
  const reboundNodes = rebindNodesWithOAuthConnections([dynamicPublicPetstoreNode], [gmailConnection]);
  assert(reboundNodes[0] === dynamicPublicPetstoreNode, 'Scenario E: Dynamic OpenAPI node is untouched by OAuth rebinder');

  console.log(`--- AI-37 Phase 39 Tests Complete: ${passed}/${total} assertions passed cleanly ---`);
  return { passed, total };
}

// Auto-run if executed directly
if (typeof window !== 'undefined') {
  (window as any).__runPhase39Tests = runOAuthReadinessPhase39Tests;
}
