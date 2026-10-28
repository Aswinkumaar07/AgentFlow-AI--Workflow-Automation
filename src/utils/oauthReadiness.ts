import type { OAuthConnection } from '../types/oauth';

export type ProviderReadinessStatus = 'READY' | 'MISSING_CONNECTION' | 'INTERNAL_PROVIDER' | 'UNKNOWN_PROVIDER';

export interface ProviderReadinessResult {
  provider: string;
  status: ProviderReadinessStatus;
  requires_oauth: boolean;
}

export interface WorkflowReadinessResult {
  ready: boolean;
  missing_connections: string[];
  provider_results: ProviderReadinessResult[];
}

const INTERNAL_PROVIDERS = new Set([
  'ai',
  'schedule',
  'condition',
  'loop',
  'merge',
  'approval',
  'human_approval',
  'human approval',
  'webhook',
  'code',
  'trigger',
  'internal',
  'agentflow',
  'generic',
]);

const GOOGLE_VARIANTS = new Set([
  'google',
  'gmail',
  'google_gmail',
  'google_drive',
  'drive',
  'google_sheets',
  'sheets',
]);

export function isInternalProvider(provider: string): boolean {
  if (!provider) return true;
  const norm = provider.toLowerCase().trim();
  return INTERNAL_PROVIDERS.has(norm) || norm.startsWith('internal') || norm.startsWith('ai_');
}

export function isGoogleService(provider: string): boolean {
  if (!provider) return false;
  const norm = provider.toLowerCase().trim();
  return GOOGLE_VARIANTS.has(norm) || norm.includes('google') || norm.includes('gmail') || norm.includes('drive') || norm.includes('sheets');
}

export function isDynamicOpenAPIOperation(nodeOrData: any): boolean {
  if (!nodeOrData) return false;
  const data = typeof nodeOrData === 'object' && nodeOrData.data ? nodeOrData.data : nodeOrData;
  const params = (data && data.parameters) || (typeof nodeOrData === 'object' && nodeOrData.parameters) || {};

  const isDynamic = Boolean(
    data?.is_dynamic_api ||
    params?.is_dynamic_api ||
    data?.provider === 'generic_rest' ||
    params?.provider === 'generic_rest' ||
    (typeof data?.provider === 'string' && data.provider.toLowerCase().includes('openapi')) ||
    (typeof params?.provider === 'string' && params.provider.toLowerCase().includes('openapi'))
  );

  return isDynamic;
}

export function isDynamicPublicOpenAPIOperation(nodeOrData: any): boolean {
  if (!isDynamicOpenAPIOperation(nodeOrData)) return false;

  const data = typeof nodeOrData === 'object' && nodeOrData.data ? nodeOrData.data : nodeOrData;
  const params = (data && data.parameters) || (typeof nodeOrData === 'object' && nodeOrData.parameters) || {};

  const secSchemes = data?.security_schemes || params?.security_schemes || {};
  const secReqs = data?.security_requirements || params?.security_requirements || [];

  const hasSecSchemes = typeof secSchemes === 'object' && secSchemes !== null && Object.keys(secSchemes).length > 0;
  const hasSecReqs = Array.isArray(secReqs) && secReqs.length > 0;

  return !hasSecSchemes && !hasSecReqs;
}

export function checkNodeReadiness(
  nodes: any[],
  connections: OAuthConnection[] = []
): WorkflowReadinessResult {
  const missing_connections: string[] = [];
  const provider_results: ProviderReadinessResult[] = [];

  const activeConnections = connections.filter((c) => c && (c.status === 'CONNECTED' || (c as any).is_connected === true));

  for (const node of nodes) {
    if (!node) continue;
    const data = node.data || node;
    const provider = data.provider || node.provider || '';
    if (!provider) continue;

    const norm = provider.toLowerCase().trim();

    // Internal providers (AI, Condition, Loop, Merge, Schedule, Approval, Webhook, etc.)
    if (isInternalProvider(norm)) {
      provider_results.push({
        provider,
        status: 'INTERNAL_PROVIDER',
        requires_oauth: false,
      });
      continue;
    }

    // Dynamic OpenAPI operations (is_dynamic_api = true or generic_rest)
    if (isDynamicOpenAPIOperation(node)) {
      // Dynamic OpenAPI operations (public or authenticated) are handled by backend runtime/GenericRESTAdapter, not native OAuth store
      provider_results.push({
        provider,
        status: 'READY',
        requires_oauth: false,
      });
      continue;
    }

    // Native OAuth Connectors (Gmail, Slack, Drive, Sheets, GitHub, Stripe, Notion, etc.)
    const isConnected = activeConnections.some((c) => {
      if (!c || !c.provider) return false;
      const cNorm = c.provider.toLowerCase().trim();
      if (cNorm === norm) return true;
      if (isGoogleService(norm) && isGoogleService(cNorm)) return true;
      return norm.includes(cNorm) || cNorm.includes(norm);
    });

    if (isConnected) {
      provider_results.push({
        provider,
        status: 'READY',
        requires_oauth: true,
      });
    } else {
      if (!missing_connections.includes(provider)) {
        missing_connections.push(provider);
      }
      provider_results.push({
        provider,
        status: 'MISSING_CONNECTION',
        requires_oauth: true,
      });
    }
  }

  return {
    ready: missing_connections.length === 0,
    missing_connections,
    provider_results,
  };
}

export function checkProviderReadiness(
  requiredProvidersOrNodes: (string | any)[],
  connections: OAuthConnection[] = []
): WorkflowReadinessResult {
  if (Array.isArray(requiredProvidersOrNodes) && requiredProvidersOrNodes.length > 0 && typeof requiredProvidersOrNodes[0] === 'object') {
    return checkNodeReadiness(requiredProvidersOrNodes, connections);
  }

  const missing_connections: string[] = [];
  const provider_results: ProviderReadinessResult[] = [];

  const activeConnections = connections.filter((c) => c && (c.status === 'CONNECTED' || (c as any).is_connected === true));

  for (const rawProv of requiredProvidersOrNodes) {
    if (!rawProv || typeof rawProv !== 'string') continue;
    const norm = rawProv.toLowerCase().trim();

    if (isInternalProvider(norm)) {
      provider_results.push({
        provider: rawProv,
        status: 'INTERNAL_PROVIDER',
        requires_oauth: false,
      });
      continue;
    }

    if (norm === 'generic_rest' || norm.includes('openapi')) {
      provider_results.push({
        provider: rawProv,
        status: 'READY',
        requires_oauth: false,
      });
      continue;
    }

    const isConnected = activeConnections.some((c) => {
      if (!c || !c.provider) return false;
      const cNorm = c.provider.toLowerCase().trim();
      if (cNorm === norm) return true;
      if (isGoogleService(norm) && isGoogleService(cNorm)) return true;
      return norm.includes(cNorm) || cNorm.includes(norm);
    });

    if (isConnected) {
      provider_results.push({
        provider: rawProv,
        status: 'READY',
        requires_oauth: true,
      });
    } else {
      missing_connections.push(rawProv);
      provider_results.push({
        provider: rawProv,
        status: 'MISSING_CONNECTION',
        requires_oauth: true,
      });
    }
  }

  return {
    ready: missing_connections.length === 0,
    missing_connections,
    provider_results,
  };
}

export function normalizeAccountLabel(_provider?: string, label?: string): string | undefined {
  if (!label) return label;
  if (/^slack_.*@slack\.com$/i.test(label.trim())) {
    return 'Slack Workspace';
  }
  return label;
}

/**
 * Rebinds workflow nodes with active OAuth connections.
 * Inspects only nodes requiring OAuth (never internal providers like AI, Condition, Loop, etc.).
 * Updates ONLY authentication parameters: credential_id, auth_status, auth_account_label.
 * Preserves all other node parameters, properties, positions, edges, etc.
 */
export function rebindNodesWithOAuthConnections(
  nodes: any[],
  connections: OAuthConnection[] = []
): any[] {
  if (!Array.isArray(nodes) || nodes.length === 0) return nodes;

  const activeConnections = Array.isArray(connections)
    ? connections.filter(
        (c) => c && (c.status === 'CONNECTED' || (c as any).is_connected === true)
      )
    : [];

  return nodes.map((node) => {
    if (!node) return node;

    const provider = node.data?.provider || node.provider || '';

    // Requirement D: Internal providers & dynamic OpenAPI operations are never OAuth-bound
    if (!provider || isInternalProvider(provider) || isDynamicOpenAPIOperation(node)) {
      return node;
    }

    const normNode = provider.toLowerCase().trim();

    // Find matching connected OAuth connection from real connections list
    const matchingConn = activeConnections.find((c) => {
      if (!c || !c.provider) return false;
      const normConn = c.provider.toLowerCase().trim();
      if (normNode === normConn) return true;
      if (isGoogleService(normNode) && isGoogleService(normConn)) return true;
      return normNode.includes(normConn) || normConn.includes(normNode);
    });

    const currentParams = node.data?.parameters || node.parameters || {};

    let updatedParams: Record<string, any>;
    if (matchingConn) {
      const rawLabel =
        matchingConn.account_label ||
        (matchingConn as any).auth_account_label ||
        (matchingConn as any).email ||
        matchingConn.provider;

      const label = normalizeAccountLabel(matchingConn.provider, rawLabel);

      updatedParams = {
        ...currentParams,
        credential_id: matchingConn.id,
        auth_status: 'active',
        auth_account_label: label,
      };

      updatedParams = {
        ...currentParams,
        credential_id: matchingConn.id,
        auth_status: 'active',
        auth_account_label: label,
      };
    } else {
      updatedParams = {
        ...currentParams,
        credential_id: null,
        auth_status: 'unbound',
        auth_account_label: null,
      };
    }

    // Preserve node structure, updating parameters inside node.data and node.parameters if present
    const updatedData = {
      ...(node.data || {}),
      parameters: updatedParams,
    };

    const updatedNode = {
      ...node,
      data: updatedData,
    };

    if (node.parameters) {
      updatedNode.parameters = updatedParams;
    }

    return updatedNode;
  });
}

