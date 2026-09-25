import { isInternalProvider, isGoogleService } from './oauthReadiness';
import type { OAuthConnection } from '../types/oauth';

export function deriveDynamicOAuthStatus(nodes: any[], connections: OAuthConnection[] = []) {
  if (!nodes || nodes.length === 0) return null;

  const steps = nodes.map((n) => {
    const data = n.data || {};
    const provider = data.provider || n.provider || 'Generic';
    const parameters = data.parameters || n.parameters || {};
    return {
      id: n.id,
      step_id: n.id,
      provider,
      parameters,
    };
  });

  const activeConnections = Array.isArray(connections)
    ? connections.filter((c) => c && (c.status === 'CONNECTED' || (c as any).is_connected === true))
    : [];

  const isNodeBound = (nodeParams: any, provider: string): boolean => {
    if (nodeParams?.auth_account_label || nodeParams?.credential_id || nodeParams?.auth_status === 'active') {
      return true;
    }
    if (!provider) return false;
    const normNode = provider.trim().toLowerCase();
    return activeConnections.some((c) => {
      if (!c || !c.provider) return false;
      const normConn = c.provider.trim().toLowerCase();
      if (normNode === normConn) return true;
      if (isGoogleService(normNode) && isGoogleService(normConn)) return true;
      return normNode.includes(normConn) || normConn.includes(normNode);
    });
  };

  const oauthSteps = steps.filter((s) => !isInternalProvider(s.provider));

  if (oauthSteps.length > 0) {
    const boundCount = oauthSteps.filter((s) => isNodeBound(s.parameters, s.provider)).length;
    const unboundSteps = oauthSteps.filter((s) => !isNodeBound(s.parameters, s.provider));

    const seenProviders = new Set<string>();
    const needsAuth: Array<{ step_id: string; provider: string; oauth_connect_url: string }> = [];
    for (const s of unboundSteps) {
      const norm = s.provider.trim().toLowerCase();
      if (!seenProviders.has(norm)) {
        seenProviders.add(norm);
        needsAuth.push({
          step_id: s.id,
          provider: s.provider,
          oauth_connect_url: '',
        });
      }
    }

    return {
      bound: boundCount,
      total: oauthSteps.length,
      needsAuth,
    };
  } else if (steps.length > 0) {
    return {
      bound: steps.length,
      total: steps.length,
      needsAuth: [],
    };
  }

  return null;
}

export function runOAuthSidebarStateTests() {
  console.log('--- Running Dynamic OAuth Sidebar State Unit Tests ---');
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

  const gmailListNode = {
    id: 'step_1',
    data: {
      provider: 'gmail',
      parameters: {},
    },
  };

  const gmailGetNode = {
    id: 'step_2',
    data: {
      provider: 'gmail',
      parameters: {},
    },
  };

  const aiNode = {
    id: 'step_3',
    data: {
      provider: 'ai',
      parameters: {},
    },
  };

  const activeGoogleConn: OAuthConnection = {
    id: 'conn_google_usr_1',
    user_id: 'usr_1',
    provider: 'Google',
    status: 'CONNECTED',
    scopes: ['gmail.readonly'],
    created_at: Date.now(),
    account_label: 'aswinkumaar07@gmail.com',
  };

  // Test 1: Connected State (Active connection present)
  const state1 = deriveDynamicOAuthStatus([gmailListNode, gmailGetNode, aiNode], [activeGoogleConn]);
  assert(state1 !== null, 'Test 1: Result is not null');
  assert(state1?.bound === 2, 'Test 1: 2 Gmail nodes auto-bound');
  assert(state1?.total === 2, 'Test 1: Total 2 OAuth nodes');
  assert(state1?.needsAuth.length === 0, 'Test 1: 0 providers require connection');

  // Test 2: Disconnected State (No connection present)
  const state2 = deriveDynamicOAuthStatus([gmailListNode, gmailGetNode, aiNode], []);
  assert(state2 !== null, 'Test 2: Result is not null');
  assert(state2?.bound === 0, 'Test 2: 0 nodes bound');
  assert(state2?.total === 2, 'Test 2: Total 2 OAuth nodes');
  assert(state2?.needsAuth.length === 1, 'Test 2: 1 provider (gmail) requires connection');
  assert(state2?.needsAuth[0].provider === 'gmail', 'Test 2: Requires connection for gmail');

  // Test 3: State Transition (Empty -> Connected)
  let connections: OAuthConnection[] = [];
  const state3a = deriveDynamicOAuthStatus([gmailListNode, gmailGetNode, aiNode], connections);
  assert(state3a?.bound === 0, 'Test 3a: Initially 0 bound');
  connections = [activeGoogleConn];
  const state3b = deriveDynamicOAuthStatus([gmailListNode, gmailGetNode, aiNode], connections);
  assert(state3b?.bound === 2, 'Test 3b: Dynamically updates to 2 bound on connection store change');
  assert(state3b?.needsAuth.length === 0, 'Test 3b: Dynamically clears requires connection list');

  // Test 4: Node parameters explicit active status
  const boundGmailNode = {
    id: 'step_1',
    data: {
      provider: 'gmail',
      parameters: {
        credential_id: 'conn_google_usr_1',
        auth_status: 'active',
        auth_account_label: 'aswinkumaar07@gmail.com',
      },
    },
  };
  const state4 = deriveDynamicOAuthStatus([boundGmailNode, aiNode], []);
  assert(state4?.bound === 1, 'Test 4: Node with explicit active parameters is recognized as bound even if store connections array is empty');
  assert(state4?.needsAuth.length === 0, 'Test 4: 0 providers require connection');

  console.log(`--- SUCCESS: All ${passed}/${total} Dynamic OAuth Sidebar State unit tests passed! ---`);
  return { passed, total };
}

runOAuthSidebarStateTests();
