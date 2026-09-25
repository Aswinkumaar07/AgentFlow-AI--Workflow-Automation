import React, { useState } from 'react';
import type { OAuthProvider, OAuthConnection, OAuthHealthStatus } from '../../types/oauth';
import type { ConnectorMetadata } from '../../api/connectors';
import { normalizeAccountLabel } from '../../utils/oauthReadiness';
import { credentialsApi, type TestConnectionResult } from '../../api/credentials';
import { oauthApi } from '../../api/oauth';
import { useOAuthStore } from '../../store/useOAuthStore';
import { DisconnectModal } from '../oauth/DisconnectModal';
import {
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Clock,
  Unlink,
  RefreshCw,
  Zap,
  ExternalLink,
  Activity,
  ChevronRight,
  Layers,
} from 'lucide-react';

interface ConnectorCardProps {
  provider: OAuthProvider;
  connection?: OAuthConnection;
  health?: OAuthHealthStatus;
  connectorDef?: ConnectorMetadata | null;
  onOpenSchemaModal: (provider: OAuthProvider, def?: ConnectorMetadata | null) => void;
}

const HEALTH_CONFIG = {
  healthy: {
    color: 'text-[#22C55E]',
    bg: 'bg-[#22C55E]/10',
    border: 'border-[#22C55E]/25',
    glow: 'shadow-[0_0_12px_rgba(34,197,94,0.15)]',
    label: 'CONNECTED',
    icon: CheckCircle2,
  },
  expiring_soon: {
    color: 'text-[#F59E0B]',
    bg: 'bg-[#F59E0B]/10',
    border: 'border-[#F59E0B]/30',
    glow: 'shadow-[0_0_12px_rgba(245,158,11,0.15)]',
    label: 'EXPIRING SOON',
    icon: AlertTriangle,
  },
  expired: {
    color: 'text-[#EF4444]',
    bg: 'bg-[#EF4444]/10',
    border: 'border-[#EF4444]/30',
    glow: 'shadow-[0_0_12px_rgba(239,68,68,0.15)]',
    label: 'EXPIRED TOKEN',
    icon: ShieldAlert,
  },
  missing: {
    color: 'text-[rgba(255,255,255,0.45)]',
    bg: 'bg-[rgba(255,255,255,0.05)]',
    border: 'border-[rgba(255,255,255,0.1)]',
    glow: '',
    label: 'NOT CONNECTED',
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

function formatExpiry(seconds: number): string {
  if (seconds <= 0) return 'Expired';
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  return `${Math.floor(seconds / 86400)}d`;
}

export const ConnectorCard: React.FC<ConnectorCardProps> = ({
  provider,
  connection,
  health,
  connectorDef,
  onOpenSchemaModal,
}) => {
  const { disconnectProvider, refreshConnection, isRefreshing } = useOAuthStore();

  const [isDisconnectModalOpen, setIsDisconnectModalOpen] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestConnectionResult | null>(null);

  const isConnected = !!connection && connection.status === 'CONNECTED';
  const isRefreshingThis = isRefreshing[provider.name] ?? false;

  const healthStatus = health?.status ?? (isConnected ? 'healthy' : 'missing');
  const hCfg = HEALTH_CONFIG[healthStatus] ?? HEALTH_CONFIG.missing;
  const HealthIcon = hCfg.icon;

  const brand = PROVIDER_BRAND_BADGES[provider.name.toLowerCase()] ?? {
    bg: 'bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/20 border-[#FF6D00]/40',
    text: 'text-[#FF6D00]',
  };

  const rawAccountLabel = connection?.account_label || health?.email_or_name;
  const accountLabel = normalizeAccountLabel(provider.name, rawAccountLabel || undefined);

  const operationsCount = connectorDef?.supported_operations
    ? connectorDef.supported_operations.length
    : connectorDef?.operation_schemas
    ? Object.keys(connectorDef.operation_schemas).length
    : 0;

  const handleConnect = async () => {
    try {
      await oauthApi.connectAccount(provider.name);
    } catch (err: any) {
      console.error(`[CONNECTORS] Failed to connect ${provider.name}:`, err);
    }
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

  const handleRefresh = async () => {
    await refreshConnection(provider.name);
  };

  const handleDisconnectConfirm = async () => {
    await disconnectProvider(provider.name);
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

        {/* Main Content Area */}
        <div className="p-5 space-y-4 flex-1">
          {/* Header Row */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div
                className={`h-12 w-12 rounded-2xl border flex items-center justify-center font-extrabold text-lg shadow-md ${brand.bg} ${brand.text}`}
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

          {/* Account Identity Section */}
          {isConnected ? (
            <div className="p-3.5 rounded-xl bg-[#1B1728]/80 border border-[rgba(255,255,255,0.08)] flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="h-7 w-7 rounded-full bg-[#22C55E]/15 text-[#22C55E] font-bold text-xs flex items-center justify-center shrink-0">
                  {accountLabel?.[0]?.toUpperCase() ?? 'A'}
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-xs text-white truncate">
                    {accountLabel || 'Connected Account'}
                  </p>
                  <p className="text-[10px] text-[rgba(255,255,255,0.45)]">Active OAuth Identity</p>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/20 font-semibold shrink-0">
                Active
              </span>
            </div>
          ) : (
            <div className="p-3.5 rounded-xl bg-[rgba(255,255,255,0.02)] border border-dashed border-[rgba(255,255,255,0.1)] text-center">
              <p className="text-xs text-[rgba(255,255,255,0.5)]">No active OAuth connection found</p>
            </div>
          )}

          {/* Operations & Schema Trigger */}
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-1.5 text-xs text-[rgba(255,255,255,0.6)]">
              <Layers className="h-4 w-4 text-[#FF6D00]" />
              <span>
                {operationsCount > 0 ? `${operationsCount} Operations Configured` : 'API Schema Registered'}
              </span>
            </div>
            <button
              onClick={() => onOpenSchemaModal(provider, connectorDef)}
              className="text-xs font-semibold text-[#FF6D00] hover:text-[#FF801A] hover:underline flex items-center gap-1 transition"
            >
              <span>View Schema</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Scopes Section */}
          {provider.scopes && provider.scopes.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <p className="text-[10px] uppercase font-bold text-[rgba(255,255,255,0.4)] tracking-wider">
                OAuth Scopes ({provider.scopes.length})
              </p>
              <div className="flex flex-wrap gap-1 max-h-16 overflow-y-auto pr-1">
                {provider.scopes.map((sc, i) => (
                  <span
                    key={i}
                    className="text-[10px] font-mono px-2 py-0.5 rounded bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.08)] text-[rgba(255,255,255,0.7)] truncate max-w-[200px]"
                    title={sc}
                  >
                    {sc}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Test Result Callout */}
          {testResult && (
            <div
              className={`p-3 rounded-xl text-xs border ${
                testResult.is_connected
                  ? 'bg-[#22C55E]/10 border-[#22C55E]/30 text-white'
                  : 'bg-rose-500/10 border-rose-500/30 text-white'
              }`}
            >
              <div className="flex items-center justify-between font-bold">
                <span className="flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5" />
                  {testResult.is_connected ? 'Connection Verified' : 'Connection Failed'}
                </span>
                <span className="font-mono text-[10px]">
                  {testResult.latency_ms > 0 ? `${testResult.latency_ms}ms` : '0ms'}
                </span>
              </div>
              <p className="text-[11px] text-[rgba(255,255,255,0.7)] mt-1">{testResult.message}</p>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-[#0E0918]/60 border-t border-[rgba(255,255,255,0.06)] flex items-center justify-between gap-2">
          {isConnected ? (
            <>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={handleTestConnection}
                  disabled={isTesting}
                  className="px-3 py-1.5 rounded-lg bg-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.12)] border border-[rgba(255,255,255,0.1)] text-white text-xs font-semibold transition flex items-center gap-1.5 disabled:opacity-50"
                  title="Test active connection"
                >
                  <Activity className={`h-3.5 w-3.5 ${isTesting ? 'animate-spin' : ''}`} />
                  <span>{isTesting ? 'Testing…' : 'Test'}</span>
                </button>

                <button
                  onClick={handleRefresh}
                  disabled={isRefreshingThis}
                  className="p-1.5 rounded-lg bg-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.12)] border border-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.7)] hover:text-white transition disabled:opacity-50"
                  title="Refresh OAuth token"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${isRefreshingThis ? 'animate-spin' : ''}`} />
                </button>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleConnect}
                  className="px-3 py-1.5 rounded-lg bg-[#FF6D00]/20 hover:bg-[#FF6D00]/30 border border-[#FF6D00]/40 text-[#FF6D00] text-xs font-semibold transition flex items-center gap-1"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  <span>Reconnect</span>
                </button>

                <button
                  onClick={() => setIsDisconnectModalOpen(true)}
                  className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 transition"
                  title="Disconnect account"
                >
                  <Unlink className="h-3.5 w-3.5" />
                </button>
              </div>
            </>
          ) : (
            <button
              onClick={handleConnect}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-black font-extrabold text-xs tracking-wide shadow-[0_4px_16px_rgba(255,109,0,0.3)] hover:opacity-90 transition flex items-center justify-center gap-2"
            >
              <Zap className="h-4 w-4 fill-current" />
              <span>Connect {provider.name}</span>
            </button>
          )}
        </div>
      </div>

      <DisconnectModal
        isOpen={isDisconnectModalOpen}
        providerName={provider.name}
        onConfirm={handleDisconnectConfirm}
        onClose={() => setIsDisconnectModalOpen(false)}
      />
    </>
  );
};
