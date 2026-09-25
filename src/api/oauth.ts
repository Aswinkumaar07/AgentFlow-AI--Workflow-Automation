import { apiClient } from './client';
import type {
  OAuthConnection,
  OAuthProvider,
  OAuthHealthStatus,
  ConnectedAccount,
} from '../types/oauth';
import { normalizeAccountLabel } from '../utils/oauthReadiness';

const unwrap = <T>(res: any): T => {
  return res?.data?.data ?? res?.data ?? res;
};

export const oauthApi = {
  // ── Single Source of Truth Backend Endpoints ───────────────
  getProviders: async (): Promise<OAuthProvider[]> => {
    try {
      const res = await apiClient.get<any>('/oauth/providers');
      const data = unwrap<OAuthProvider[]>(res);
      console.log('[AUTH-6] OAuth providers loaded:', data);
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.error('[AUTH-6] Error fetching OAuth providers:', err);
      return [];
    }
  },

  getConnections: async (): Promise<OAuthConnection[]> => {
    try {
      const res = await apiClient.get<any>('/oauth/connections');
      const data = unwrap<OAuthConnection[]>(res);
      console.log('[AUTH-6] OAuth connections loaded:', data);
      if (Array.isArray(data)) {
        return data.map((c) => ({
          ...c,
          account_label: normalizeAccountLabel(c.provider, c.account_label),
        }));
      }
      return [];
    } catch (err) {
      console.error('[AUTH-6] Error fetching OAuth connections:', err);
      return [];
    }
  },

  getHealthStatus: async (): Promise<OAuthHealthStatus[]> => {
    try {
      const res = await apiClient.get<any>('/oauth/connections/health');
      const data = unwrap<OAuthHealthStatus[]>(res);
      console.log('[AUTH-6] OAuth connection health loaded:', data);
      if (Array.isArray(data)) {
        return data.map((h) => ({
          ...h,
          email_or_name: normalizeAccountLabel(h.provider, h.email_or_name ?? undefined),
        }));
      }
      return [];
    } catch (err) {
      console.error('[AUTH-6] Error fetching OAuth connection health:', err);
      return [];
    }
  },

  // ── Backend-Driven Login URL Retrieval (Phase 1) ───────────
  getLoginUrl: async (provider: string): Promise<string> => {
    try {
      console.log(`[AUTH-6] OAuth login requested for '${provider}'`);
      const res = await apiClient.get<any>(`/oauth/${encodeURIComponent(provider.toLowerCase())}/login`);
      const data = unwrap<{ provider: string; url: string }>(res);
      console.log(`[AUTH-6] Backend-generated OAuth login URL received for '${provider}':`, data.url);
      return data.url;
    } catch (err) {
      console.error(`[AUTH-6] Failed to fetch login URL for '${provider}':`, err);
      throw err;
    }
  },

  // ── Backend-Driven Redirect (Phase 1 & Phase 2) ───────────
  connectAccount: async (provider: string): Promise<void> => {
    console.log(`[AUTH-6] Initiating backend OAuth login flow for '${provider}'...`);
    const loginUrl = await oauthApi.getLoginUrl(provider);
    if (!loginUrl) {
      throw new Error(`Failed to retrieve OAuth login URL for provider '${provider}'.`);
    }
    console.log(`[AUTH-6] Redirecting browser to backend URL: ${loginUrl}`);
    window.location.href = loginUrl;
  },

  disconnect: async (provider: string): Promise<boolean> => {
    try {
      await apiClient.post('/oauth/disconnect', { provider });
      console.log(`[AUTH-6] Disconnected provider '${provider}' via backend API`);
      return true;
    } catch (err) {
      console.error(`[AUTH-6] Error disconnecting provider '${provider}':`, err);
      return false;
    }
  },

  refreshConnection: async (provider: string): Promise<OAuthConnection | null> => {
    try {
      const res = await apiClient.post<any>('/oauth/refresh', { provider });
      const conn = unwrap<OAuthConnection>(res);
      console.log(`[AUTH-6] Refreshed connection for '${provider}' via backend API:`, conn);
      if (conn) {
        return {
          ...conn,
          account_label: normalizeAccountLabel(conn.provider, conn.account_label),
        };
      }
      return null;
    } catch (err) {
      console.error(`[AUTH-6] Error refreshing connection for '${provider}':`, err);
      return null;
    }
  },

  // ── Pure Backend Connection Listing ──────────────────────
  listAccounts: async (provider: string): Promise<ConnectedAccount[]> => {
    try {
      const res = await apiClient.get<any>('/oauth/connections');
      const data = unwrap<any[]>(res);
      if (Array.isArray(data)) {
        return data
          .filter((c) => c.provider?.toLowerCase() === provider.toLowerCase())
          .map((c) => {
            const rawLabel = c.account_label || c.email || '';
            const normalized = normalizeAccountLabel(c.provider, rawLabel) || '';
            return {
              account_id: c.id,
              provider: c.provider,
              email_or_name: normalized,
              status: c.status === 'CONNECTED' ? 'active' : 'expired',
              is_default: true,
              expires_at: c.expires_at || 0,
              scopes: c.scopes || [],
              is_expired: !!c.is_expired,
              expires_in_seconds: c.expires_in_seconds || 0,
            };
          });
      }
      return [];
    } catch (err) {
      console.error(`[AUTH-6] Error listing accounts for '${provider}':`, err);
      return [];
    }
  },
};
