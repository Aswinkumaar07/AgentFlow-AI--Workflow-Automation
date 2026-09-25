import { create } from 'zustand';
import type { OAuthConnection, OAuthProvider, ConnectedAccount, OAuthHealthStatus } from '../types/oauth';
import { oauthApi } from '../api/oauth';
import { credentialsApi } from '../api/credentials';
import { normalizeAccountLabel } from '../utils/oauthReadiness';

interface OAuthState {
  providers: OAuthProvider[];
  connections: OAuthConnection[];
  healthStatus: OAuthHealthStatus[];
  accountsByProvider: Record<string, ConnectedAccount[]>;
  isLoading: boolean;
  isRefreshing: Record<string, boolean>;

  // Fetch
  fetchOAuthData: () => Promise<void>;
  fetchHealthStatus: () => Promise<void>;
  fetchProviderAccounts: (provider: string) => Promise<void>;

  // Connection management
  disconnectProvider: (provider: string) => Promise<void>;
  refreshConnection: (provider: string) => Promise<void>;

  // Account management
  setDefaultAccount: (provider: string, accountId: string) => Promise<void>;
  disconnectAccount: (provider: string, accountId: string) => Promise<void>;

  // Helpers
  getHealthForProvider: (providerName: string) => OAuthHealthStatus | undefined;
  getAccountsForProvider: (provider: string) => ConnectedAccount[];
}

export const useOAuthStore = create<OAuthState>((set, get) => ({
  providers: [],
  connections: [],
  healthStatus: [],
  accountsByProvider: {},
  isLoading: false,
  isRefreshing: {},

  fetchOAuthData: async () => {
    set({ isLoading: true });
    try {
      const [providers, connections, healthStatus, userCreds] = await Promise.all([
        oauthApi.getProviders(),
        oauthApi.getConnections(),
        oauthApi.getHealthStatus(),
        credentialsApi.listCredentials(),
      ]);

      console.log('[AUTH-6] OAuth providers loaded:', providers);
      console.log('[AUTH-6] OAuth connections loaded:', connections);
      console.log('[AUTH-6] Credentials loaded:', userCreds);

      // Merge user credentials into connections list
      const credsAsConnections: OAuthConnection[] = Array.isArray(userCreds)
        ? userCreds.map((c) => ({
            id: c.connection_id,
            user_id: 'usr_1',
            provider: c.provider,
            status: (c.is_connected ? 'CONNECTED' : 'DISCONNECTED') as 'CONNECTED' | 'DISCONNECTED',
            scopes: c.scopes || [],
            created_at: Date.now(),
            updated_at: Date.now(),
            account_label: normalizeAccountLabel(
              c.provider,
              c.account_label || (c as any).auth_account_label || (c as any).email || undefined
            ),
          }))
        : [];

      // Combine connections keeping unique entries by provider
      const connectionMap = new Map<string, OAuthConnection>();
      connections.forEach((conn) =>
        connectionMap.set(conn.provider.toLowerCase(), {
          ...conn,
          account_label: normalizeAccountLabel(conn.provider, conn.account_label),
        })
      );
      credsAsConnections.forEach((conn) =>
        connectionMap.set(conn.provider.toLowerCase(), {
          ...conn,
          account_label: normalizeAccountLabel(conn.provider, conn.account_label),
        })
      );

      const mergedConnections = Array.from(connectionMap.values());

      set({
        providers: Array.isArray(providers) ? providers : [],
        connections: mergedConnections,
        healthStatus: Array.isArray(healthStatus) ? healthStatus : [],
        isLoading: false,
      });
    } catch (err) {
      console.error('[AUTH-6] Error in fetchOAuthData:', err);
      set({ isLoading: false });
    }
  },

  fetchHealthStatus: async () => {
    try {
      const healthStatus = await oauthApi.getHealthStatus();
      console.log('[AUTH-6] Connection health status updated:', healthStatus);
      set({ healthStatus: Array.isArray(healthStatus) ? healthStatus : [] });
    } catch (err) {
      console.error('[AUTH-6] Error in fetchHealthStatus:', err);
    }
  },

  fetchProviderAccounts: async (provider: string) => {
    try {
      const accounts = await oauthApi.listAccounts(provider);
      set((state) => ({
        accountsByProvider: { ...state.accountsByProvider, [provider]: accounts },
      }));
    } catch (err) {
      console.error(`[AUTH-6] Error in fetchProviderAccounts for '${provider}':`, err);
    }
  },

  disconnectProvider: async (provider: string) => {
    try {
      await oauthApi.disconnect(provider);
      console.log(`[AUTH-6] Disconnected provider '${provider}'`);
      set((state) => ({
        connections: state.connections.filter(
          (c) => c.provider.toLowerCase() !== provider.toLowerCase()
        ),
        healthStatus: state.healthStatus.map((h) =>
          h.provider.toLowerCase().includes(provider.toLowerCase())
            ? { ...h, is_connected: false, status: 'missing' as const }
            : h
        ),
      }));
    } catch (err) {
      console.error(`[AUTH-6] Error in disconnectProvider for '${provider}':`, err);
    }
  },

  refreshConnection: async (provider: string) => {
    set((state) => ({ isRefreshing: { ...state.isRefreshing, [provider]: true } }));
    try {
      const conn = await oauthApi.refreshConnection(provider);
      if (conn) {
        console.log(`[AUTH-6] Successfully refreshed connection for '${provider}'`);
        await get().fetchOAuthData();
      }
    } catch (err) {
      console.error(`[AUTH-6] Error in refreshConnection for '${provider}':`, err);
    } finally {
      set((state) => ({ isRefreshing: { ...state.isRefreshing, [provider]: false } }));
    }
  },

  setDefaultAccount: async (provider: string, accountId: string) => {
    console.log(`[AUTH-6] Set default account '${accountId}' for '${provider}'`);
    await get().fetchProviderAccounts(provider);
  },

  disconnectAccount: async (provider: string, accountId: string) => {
    console.log(`[AUTH-6] Disconnect account '${accountId}' for '${provider}'`);
    set((state) => ({
      accountsByProvider: {
        ...state.accountsByProvider,
        [provider]: (state.accountsByProvider[provider] || []).filter(
          (a) => a.account_id !== accountId
        ),
      },
    }));
  },

  getHealthForProvider: (providerName: string) => {
    const { healthStatus } = get();
    return healthStatus.find(
      (h) =>
        h.provider?.toLowerCase().includes(providerName.toLowerCase()) ||
        providerName.toLowerCase().includes(h.provider?.toLowerCase() ?? '')
    );
  },

  getAccountsForProvider: (provider: string) => {
    return get().accountsByProvider[provider] || [];
  },
}));
