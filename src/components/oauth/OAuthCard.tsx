import React, { useState, useEffect } from 'react';
import type { OAuthConnection, OAuthProvider, ConnectedAccount, OAuthHealthStatus } from '../../types/oauth';
import { useOAuthStore } from '../../store/useOAuthStore';
import { oauthApi } from '../../api/oauth';
import { credentialsApi } from '../../api/credentials';
import type { TestConnectionResult } from '../../api/credentials';
import { DisconnectModal } from './DisconnectModal';
import { ConnectorDetailModal } from './ConnectorDetailModal';
import {
  CheckCircle2, ShieldAlert, KeyRound, ExternalLink, Unlink,
  RefreshCw, Star, ChevronDown, Clock, AlertTriangle, ShieldCheck, Zap, Activity,
  SlidersHorizontal
} from 'lucide-react';

interface OAuthCardProps {
  provider: OAuthProvider;
  connection?: OAuthConnection;
  health?: OAuthHealthStatus;
  onDisconnect: (providerName: string) => Promise<void>;
}

function formatExpiry(seconds: number): string {
  if (seconds <= 0) return 'Expired';
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  return `${Math.floor(seconds / 86400)}d`;
}

const HEALTH_CONFIG = {
  healthy: {
    color: 'text-[#22C55E]',
    bg: 'bg-[#22C55E]/10',
    border: 'border-[#22C55E]/25',
    glow: 'shadow-[0_0_12px_rgba(34,197,94,0.15)]',
    label: 'Connected',
    icon: CheckCircle2,
  },
  expiring_soon: {
    color: 'text-[#F59E0B]',
    bg: 'bg-[#F59E0B]/10',
    border: 'border-[#F59E0B]/30',
    glow: 'shadow-[0_0_12px_rgba(245,158,11,0.15)]',
    label: 'Expiring Soon',
    icon: AlertTriangle,
  },
  expired: {
    color: 'text-[#EF4444]',
    bg: 'bg-[#EF4444]/10',
    border: 'border-[#EF4444]/30',
    glow: 'shadow-[0_0_12px_rgba(239,68,68,0.15)]',
    label: 'Expired Token',
    icon: ShieldAlert,
  },
  missing: {
    color: 'text-[rgba(255,255,255,0.45)]',
    bg: 'bg-[rgba(255,255,255,0.05)]',
    border: 'border-[rgba(255,255,255,0.1)]',
    glow: '',
    label: 'Not Connected',
    icon: ShieldAlert,
  },
};

const PROVIDER_BRAND_BADGES: Record<string, { bg: string; text: string }> = {
  google: { bg: 'bg-gradient-to-br from-blue-500/20 via-red-500/20 to-yellow-500/20 border-blue-500/40', text: 'text-blue-400' },
  gmail: { bg: 'bg-gradient-to-br from-red-500/20 to-rose-600/20 border-red-500/40', text: 'text-red-400' },
  slack: { bg: 'bg-gradient-to-br from-purple-500/20 to-emerald-500/20 border-purple-500/40', text: 'text-purple-400' },
  drive: { bg: 'bg-gradient-to-br from-emerald-500/20 to-blue-500/20 border-emerald-500/40', text: 'text-emerald-400' },
  github: { bg: 'bg-gradient-to-br from-slate-600/20 to-zinc-800/20 border-slate-500/40', text: 'text-slate-300' },
  stripe: { bg: 'bg-gradient-to-br from-indigo-500/20 to-purple-600/20 border-indigo-500/40', text: 'text-indigo-400' },
};

export const OAuthCard: React.FC<OAuthCardProps> = ({ provider, connection, health, onDisconnect }) => {
  const {
    isRefreshing,
    accountsByProvider,
    refreshConnection,
    setDefaultAccount,
    disconnectAccount,
    fetchProviderAccounts,
  } = useOAuthStore();

  const [isDisconnectOpen, setIsDisconnectOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [showAccounts, setShowAccounts] = useState(false);
  const [disconnectingAccountId, setDisconnectingAccountId] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestConnectionResult | null>(null);

  const isConnected = !!connection && connection.status === 'CONNECTED';
  const isRefreshingThis = isRefreshing[provider.name] ?? false;

  const healthStatus = health?.status ?? (isConnected ? 'healthy' : 'missing');
  const hCfg = HEALTH_CONFIG[healthStatus] ?? HEALTH_CONFIG.missing;
  const HealthIcon = hCfg.icon;

  const accounts: ConnectedAccount[] = accountsByProvider[provider.name] ?? [];
  const defaultAccount = accounts.find((a) => a.is_default) ?? accounts[0];

  const brand = PROVIDER_BRAND_BADGES[provider.name.toLowerCase()] ?? {
    bg: 'bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/20 border-[#FF6D00]/40',
    text: 'text-[#FF6D00]',
  };

  useEffect(() => {
    if (isConnected && showAccounts && accounts.length === 0) {
      fetchProviderAccounts(provider.name);
    }
  }, [showAccounts, isConnected]);

  const handleConnect = async () => {
    try {
      await oauthApi.connectAccount(provider.name);
    } catch (err: any) {
      console.error(`[AUTH-6] Failed to connect account for ${provider.name}:`, err);
    }
  };

  const handleRefresh = async () => {
    await refreshConnection(provider.name);
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await credentialsApi.testConnection(provider.name, provider.auth_type);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        provider: provider.name,
        status: 'failed',
        is_connected: false,
        latency_ms: 0,
        auth_type: provider.auth_type,
        scopes: provider.scopes || [],
        message: err?.response?.data?.detail || err?.message || `Connection test failed for ${provider.name}.`,
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSetDefault = async (accountId: string) => {
    await setDefaultAccount(provider.name, accountId);
  };

  const handleDisconnectAccount = async (accountId: string) => {
    setDisconnectingAccountId(accountId);
    await disconnectAccount(provider.name, accountId);
    setDisconnectingAccountId(null);
  };

  const handleToggleAccounts = async () => {
    if (!showAccounts && accounts.length === 0) {
      await fetchProviderAccounts(provider.name);
    }
    setShowAccounts((v) => !v);
  };

  return (
    <>
      <div
        className={`rounded-2xl border bg-[#13102A]/80 backdrop-blur-md transition-all duration-300 flex flex-col justify-between overflow-hidden relative group hover:border-[#FF6D00]/50 hover:shadow-[0_8px_32px_rgba(255,109,0,0.15)] ${
          healthStatus === 'expired'
            ? 'border-rose-500/40 shadow-[0_0_20px_rgba(239,68,68,0.12)]'
            : healthStatus === 'expiring_soon'
            ? 'border-amber-500/40 shadow-[0_0_20px_rgba(245,158,11,0.12)]'
            : isConnected
            ? 'border-[rgba(255,255,255,0.12)]'
            : 'border-[rgba(255,255,255,0.08)]'
        }`}
      >
        {/* Top Accent Line */}
        <div
          className={`h-1 w-full ${
            isConnected
              ? healthStatus === 'expired'
                ? 'bg-rose-500'
                : healthStatus === 'expiring_soon'
                ? 'bg-amber-500'
                : 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00]'
              : 'bg-[rgba(255,255,255,0.08)]'
          }`}
        />

        {/* ── Main Card Content ── */}
        <div className="p-5 space-y-4 flex-1">
          {/* Header Row */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div
                className={`h-11 w-11 rounded-2xl border flex items-center justify-center font-extrabold text-base shadow-md ${brand.bg} ${brand.text}`}
              >
                {provider.name[0]?.toUpperCase() ?? '?'}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-bold text-base text-white tracking-tight">{provider.name}</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[rgba(255,255,255,0.06)] border border-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.6)] font-medium">
                    {provider.auth_type}
                  </span>
                </div>
                {health && health.expires_in_seconds > 0 && (
                  <span className="text-[11px] text-[#F59E0B] font-medium flex items-center gap-1 mt-0.5">
                    <Clock className="h-3 w-3" /> Expiry: {formatExpiry(health.expires_in_seconds)}
                  </span>
                )}
              </div>
            </div>

            {/* Health Status Pill */}
            <div
              className={`px-3 py-1 rounded-full border text-[11px] font-bold flex items-center gap-1.5 shrink-0 ${hCfg.bg} ${hCfg.color} ${hCfg.border} ${hCfg.glow}`}
            >
              <HealthIcon className="h-3.5 w-3.5" />
              {hCfg.label}
            </div>
          </div>

          {/* ── Account Identity Display ── */}
          {isConnected ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 rounded-xl bg-[#1B1728]/80 border border-[rgba(255,255,255,0.08)]">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="h-7 w-7 rounded-full bg-[#22C55E]/15 text-[#22C55E] font-bold text-xs flex items-center justify-center shrink-0">
                    {defaultAccount?.email_or_name?.[0]?.toUpperCase() ?? connection?.account_label?.[0]?.toUpperCase() ?? 'A'}
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-xs text-white truncate">
                      {defaultAccount?.email_or_name || connection?.account_label || 'Connected Account'}
                    </p>
                    <p className="text-[10px] text-[rgba(255,255,255,0.45)]">Authenticated Identity</p>
                  </div>
                </div>

                <button
                  onClick={handleToggleAccounts}
                  className="text-[11px] font-semibold text-[#FF6D00] hover:underline flex items-center gap-1 shrink-0 ml-2"
                >
                  <span>Accounts</span>
                  <ChevronDown className={`h-3 w-3 transition-transform ${showAccounts ? 'rotate-180' : ''}`} />
                </button>
              </div>

              {/* Multi-Account Drawer */}
              {showAccounts && (
                <div className="p-2.5 rounded-xl bg-[#0E0918]/80 border border-[rgba(255,255,255,0.08)] space-y-1.5 animate-in fade-in duration-150">
                  {accounts.length === 0 ? (
                    <div className="text-[11px] text-[rgba(255,255,255,0.4)] text-center py-2">Loading tenant accounts…</div>
                  ) : (
                    accounts.map((acc) => (
                      <div
                        key={acc.account_id}
                        className={`flex items-center justify-between rounded-lg px-2.5 py-1.5 text-xs border transition ${
                          acc.is_default
                            ? 'bg-[#FF6D00]/10 border-[#FF6D00]/30 text-white'
                            : 'bg-[#1B1728]/50 border-[rgba(255,255,255,0.08)] text-[rgba(255,255,255,0.7)]'
                        }`}
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="truncate font-medium">{acc.email_or_name}</span>
                          {acc.is_default && (
                            <span className="text-[9px] font-extrabold bg-[#FF6D00] text-black px-1.5 py-0.2 rounded">
                              DEFAULT
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-1 shrink-0">
                          {!acc.is_default && (
                            <button
                              onClick={() => handleSetDefault(acc.account_id)}
                              className="p-1 rounded hover:bg-[#FF6D00]/20 text-[#FF6D00] transition"
                              title="Set as Default"
                            >
                              <Star className="h-3.5 w-3.5" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDisconnectAccount(acc.account_id)}
                            disabled={disconnectingAccountId === acc.account_id}
                            className="p-1 rounded hover:bg-rose-500/20 text-rose-400 transition"
                            title="Remove Account"
                          >
                            <Unlink className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}

                  <button
                    onClick={handleConnect}
                    className="w-full text-[11px] font-semibold text-[#FF6D00] hover:underline pt-1 text-center block"
                  >
                    + Add Account
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-[#1B1728]/40 border border-[rgba(255,255,255,0.05)] text-xs text-[rgba(255,255,255,0.5)] flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-[rgba(255,255,255,0.3)] shrink-0" />
              <span>No account currently bound to this provider.</span>
            </div>
          )}

          {/* Test Ping Diagnostic Badge */}
          {testResult && (
            <div className="p-2.5 rounded-xl bg-[#22C55E]/10 border border-[#22C55E]/20 text-xs text-[#22C55E] flex items-center justify-between font-semibold animate-in fade-in duration-200">
              <span className="flex items-center gap-1.5 truncate">
                <Activity className="h-4 w-4 shrink-0" /> {testResult.message}
              </span>
              <span className="font-mono text-[10px] bg-[#22C55E]/20 px-2 py-0.5 rounded-md border border-[#22C55E]/30 shrink-0">
                {testResult.latency_ms}ms
              </span>
            </div>
          )}

          {/* ── Scopes List Chips ── */}
          <div className="space-y-1.5 pt-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[rgba(255,255,255,0.45)]">
              Authorized Scopes ({provider.scopes?.length || 0})
            </span>
            <div className="flex flex-wrap gap-1.5">
              {(provider.scopes || []).map((scope) => (
                <span
                  key={scope}
                  className="px-2 py-0.5 rounded-md bg-[#0E0918] border border-[rgba(255,255,255,0.1)] text-[10px] font-mono text-[rgba(255,255,255,0.65)]"
                >
                  {scope}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Card Footer Actions ── */}
        <div className="p-4 border-t border-[rgba(255,255,255,0.08)] bg-[#0E0918]/60 flex items-center justify-between gap-2">
          <button
            onClick={() => setIsDetailModalOpen(true)}
            className="text-[11px] font-semibold text-[rgba(255,255,255,0.6)] hover:text-white flex items-center gap-1 transition"
          >
            <SlidersHorizontal className="h-3.5 w-3.5 text-[#FF6D00]" />
            <span>Manage & Details</span>
          </button>

          <div className="flex items-center gap-1.5">
            {isConnected ? (
              <>
                <button
                  onClick={handleTestConnection}
                  disabled={isTesting}
                  className="p-2 rounded-xl border border-[#FF6D00]/30 bg-[#FF6D00]/10 hover:bg-[#FF6D00]/20 text-[#FF6D00] text-xs font-semibold transition flex items-center gap-1 disabled:opacity-50"
                  title="Test Live Connection Ping"
                >
                  <Zap className={`h-3.5 w-3.5 ${isTesting ? 'animate-spin' : ''}`} />
                </button>

                <button
                  onClick={handleRefresh}
                  disabled={isRefreshingThis}
                  className="p-2 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-[rgba(255,255,255,0.7)] hover:text-white transition disabled:opacity-50"
                  title="Force Token Refresh"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${isRefreshingThis ? 'animate-spin' : ''}`} />
                </button>

                <button
                  onClick={handleConnect}
                  className="px-3 py-1.5 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-xs font-semibold text-white transition flex items-center gap-1"
                >
                  <ExternalLink className="h-3.5 w-3.5" /> Reconnect
                </button>

                <button
                  onClick={() => setIsDisconnectOpen(true)}
                  className="p-2 rounded-xl border border-rose-500/20 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 transition"
                  title="Disconnect Provider"
                >
                  <Unlink className="h-3.5 w-3.5" />
                </button>
              </>
            ) : (
              <button
                onClick={handleConnect}
                className="px-4 py-2 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl shadow-[0_4px_16px_rgba(255,109,0,0.3)] hover:opacity-95 transition flex items-center gap-1.5"
              >
                <KeyRound className="h-3.5 w-3.5" /> Connect Account
              </button>
            )}
          </div>
        </div>
      </div>

      <DisconnectModal
        isOpen={isDisconnectOpen}
        providerName={provider.name}
        onConfirm={async () => {
          await onDisconnect(provider.name);
        }}
        onClose={() => setIsDisconnectOpen(false)}
      />

      <ConnectorDetailModal
        isOpen={isDetailModalOpen}
        provider={provider}
        connection={connection}
        health={health}
        onClose={() => setIsDetailModalOpen(false)}
        onDisconnect={onDisconnect}
      />
    </>
  );
};
