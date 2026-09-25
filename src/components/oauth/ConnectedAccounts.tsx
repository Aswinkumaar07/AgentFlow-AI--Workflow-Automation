import React, { useState, useEffect, useMemo } from 'react';
import { useOAuthStore } from '../../store/useOAuthStore';
import { OAuthCard } from './OAuthCard';
import {
  ShieldCheck, RefreshCw, Wifi, WifiOff, AlertTriangle, Search, X, Cpu
} from 'lucide-react';

export const ConnectedAccounts: React.FC = () => {
  const {
    providers,
    connections,
    healthStatus,
    isLoading,
    fetchOAuthData,
    fetchHealthStatus,
    disconnectProvider,
    getHealthForProvider,
  } = useOAuthStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<'all' | 'connected' | 'not_connected' | 'attention'>('all');

  useEffect(() => {
    fetchOAuthData();
  }, [fetchOAuthData]);

  // Auto-poll health status every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => fetchHealthStatus(), 60_000);
    return () => clearInterval(interval);
  }, [fetchHealthStatus]);

  const activeProviders = Array.isArray(providers) ? providers : [];
  const activeConnections = Array.isArray(connections) ? connections : [];
  const activeHealth = Array.isArray(healthStatus) ? healthStatus : [];

  // Summary statistics calculation
  const totalCount = activeProviders.length;
  
  const connectedCount = useMemo(() => {
    return activeProviders.filter((prov) => {
      const health = getHealthForProvider(prov.name);
      const conn = activeConnections.find(
        (c) =>
          c.provider.toLowerCase().includes(prov.id.toLowerCase()) ||
          prov.name.toLowerCase().includes(c.provider.toLowerCase())
      );
      return health?.is_connected || conn?.status === 'CONNECTED';
    }).length;
  }, [activeProviders, activeConnections, healthStatus]);

  const expiredCount = useMemo(() => {
    return activeHealth.filter((h) => h.status === 'expired' || h.is_expired).length;
  }, [activeHealth]);

  const expiringSoonCount = useMemo(() => {
    return activeHealth.filter((h) => h.status === 'expiring_soon').length;
  }, [activeHealth]);

  const attentionCount = expiredCount + expiringSoonCount;
  const notConnectedCount = Math.max(0, totalCount - connectedCount);
  const healthPercentage = totalCount > 0 ? Math.round((connectedCount / totalCount) * 100) : 100;

  // Filter & Search Logic
  const filteredProviders = useMemo(() => {
    return activeProviders.filter((prov) => {
      const conn = activeConnections.find(
        (c) =>
          c.provider.toLowerCase().includes(prov.id.toLowerCase()) ||
          prov.name.toLowerCase().includes(c.provider.toLowerCase())
      );
      const health = getHealthForProvider(prov.name);
      const isConn = health?.is_connected || conn?.status === 'CONNECTED';
      const isExpired = health?.status === 'expired' || health?.is_expired;
      const isExpiringSoon = health?.status === 'expiring_soon';

      // Category filter check
      if (filterCategory === 'connected' && !isConn) return false;
      if (filterCategory === 'not_connected' && isConn) return false;
      if (filterCategory === 'attention' && !isExpired && !isExpiringSoon) return false;

      // Text search check
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const nameMatch = prov.name.toLowerCase().includes(query);
        const typeMatch = prov.auth_type?.toLowerCase().includes(query);
        const scopeMatch = (prov.scopes || []).some((s) => s.toLowerCase().includes(query));
        const accountMatch = conn?.account_label?.toLowerCase().includes(query);
        if (!nameMatch && !typeMatch && !scopeMatch && !accountMatch) return false;
      }

      return true;
    });
  }, [activeProviders, activeConnections, healthStatus, searchQuery, filterCategory]);

  return (
    <div className="space-y-6 max-w-[1440px] mx-auto">
      
      {/* ── 1. Premium Page Header Banner ── */}
      <div className="p-6 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md shadow-[0_8px_32px_rgba(0,0,0,0.36)] flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-[#FF6D00]/10 to-[#FF0C00]/5 blur-3xl pointer-events-none rounded-full" />

        <div className="flex items-center gap-4 relative z-10">
          <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] flex items-center justify-center text-white shadow-[0_4px_20px_rgba(255,109,0,0.4)] shrink-0">
            <Cpu className="h-7 w-7 fill-current" />
          </div>

          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-extrabold text-white tracking-tight">Connectors & Integrations Workspace</h2>
              <span className="px-2.5 py-0.5 rounded-full bg-[#22C55E]/15 border border-[#22C55E]/30 text-[#22C55E] text-[10px] font-bold uppercase tracking-wider">
                {healthPercentage}% Operational
              </span>
            </div>
            <p className="text-xs text-[rgba(255,255,255,0.6)] mt-1 flex items-center gap-2 flex-wrap">
              <span className="flex items-center gap-1 text-[#22C55E]">
                <ShieldCheck className="h-3.5 w-3.5" /> AES-256 Vault Encrypted
              </span>
              <span>•</span>
              <span>Single Source of Truth</span>
              <span>•</span>
              <span>Auto Token Refresh Handshake</span>
            </p>
          </div>
        </div>

        {/* Refresh Sync Button */}
        <div className="flex items-center gap-3 relative z-10 self-start md:self-auto">
          <button
            onClick={fetchOAuthData}
            disabled={isLoading}
            className="px-4 py-2.5 rounded-xl border border-[rgba(255,255,255,0.15)] bg-[#1B1728] hover:bg-[#231E3A] hover:border-[#FF6D00]/50 text-xs font-bold text-white transition flex items-center gap-2 shadow-md disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 text-[#FF6D00] ${isLoading ? 'animate-spin' : ''}`} />
            <span>Sync Credentials</span>
          </button>
        </div>
      </div>

      {/* ── Metric Summary Cards Bar ── */}
      {!isLoading && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl border border-[#22C55E]/20 bg-[#22C55E]/5 backdrop-blur-md flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-[#22C55E]/10 text-[#22C55E] flex items-center justify-center shrink-0">
              <Wifi className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xl font-extrabold text-white">{connectedCount} <span className="text-xs font-normal text-[rgba(255,255,255,0.4)]">/ {totalCount}</span></p>
              <p className="text-[11px] font-semibold text-[#22C55E]">Active Connected</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[#13102A]/60 backdrop-blur-md flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-[rgba(255,255,255,0.05)] text-[rgba(255,255,255,0.6)] flex items-center justify-center shrink-0">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xl font-extrabold text-white">{notConnectedCount}</p>
              <p className="text-[11px] font-semibold text-[rgba(255,255,255,0.5)]">Not Connected</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl border border-[#F59E0B]/20 bg-[#F59E0B]/5 backdrop-blur-md flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-[#F59E0B]/10 text-[#F59E0B] flex items-center justify-center shrink-0">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xl font-extrabold text-[#F59E0B]">{expiringSoonCount}</p>
              <p className="text-[11px] font-semibold text-[#F59E0B]">Expiring Soon</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl border border-rose-500/20 bg-rose-500/5 backdrop-blur-md flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center shrink-0">
              <WifiOff className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xl font-extrabold text-rose-400">{expiredCount}</p>
              <p className="text-[11px] font-semibold text-rose-400">Tokens Expired</p>
            </div>
          </div>
        </div>
      )}

      {/* ── 2. Search + Filter Toolbar ── */}
      <div className="p-4 rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        
        {/* Search Bar */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(255,255,255,0.4)]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search connectors by provider, auth type, or scope..."
            className="w-full pl-10 pr-9 py-2 rounded-xl bg-[#1B1728] border border-[rgba(255,255,255,0.1)] text-xs text-white placeholder-[rgba(255,255,255,0.4)] focus:outline-none focus:border-[#FF6D00] focus:ring-1 focus:ring-[#FF6D00] transition"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-md text-[rgba(255,255,255,0.4)] hover:text-white hover:bg-[rgba(255,255,255,0.1)]"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Filter Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1">
          {[
            { id: 'all', label: 'All', count: totalCount },
            { id: 'connected', label: 'Connected', count: connectedCount },
            { id: 'not_connected', label: 'Not Connected', count: notConnectedCount },
            { id: 'attention', label: 'Needs Attention', count: attentionCount },
          ].map((pill) => {
            const isAct = filterCategory === pill.id;
            return (
              <button
                key={pill.id}
                onClick={() => setFilterCategory(pill.id as any)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition whitespace-nowrap ${
                  isAct
                    ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-[0_4px_12px_rgba(255,109,0,0.3)]'
                    : 'bg-[#1B1728] text-[rgba(255,255,255,0.6)] hover:bg-[#231E3A] hover:text-white border border-[rgba(255,255,255,0.08)]'
                }`}
              >
                <span>{pill.label}</span>
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                    isAct ? 'bg-black/30 text-white' : 'bg-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.7)]'
                  }`}
                >
                  {pill.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── 3. Connector Cards Grid & Loading States ── */}
      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="h-56 rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[#13102A]/60 backdrop-blur-md animate-pulse p-6 space-y-4"
            >
              <div className="flex justify-between items-center">
                <div className="flex gap-3 items-center">
                  <div className="h-10 w-10 rounded-2xl bg-[rgba(255,255,255,0.06)]" />
                  <div className="space-y-2">
                    <div className="h-4 w-28 rounded bg-[rgba(255,255,255,0.06)]" />
                    <div className="h-3 w-16 rounded bg-[rgba(255,255,255,0.04)]" />
                  </div>
                </div>
                <div className="h-6 w-20 rounded-full bg-[rgba(255,255,255,0.06)]" />
              </div>
              <div className="h-12 rounded-xl bg-[rgba(255,255,255,0.04)]" />
              <div className="h-8 rounded-xl bg-[rgba(255,255,255,0.06)]" />
            </div>
          ))}
        </div>
      ) : filteredProviders.length === 0 ? (
        /* ── Empty State ── */
        <div className="p-12 text-center border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-md rounded-3xl space-y-4 max-w-md mx-auto my-8">
          <div className="h-16 w-16 rounded-3xl bg-[rgba(255,255,255,0.05)] text-[rgba(255,255,255,0.4)] flex items-center justify-center mx-auto border border-[rgba(255,255,255,0.1)]">
            <Search className="h-8 w-8" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">No connectors match your criteria</h3>
            <p className="text-xs text-[rgba(255,255,255,0.5)] mt-1">
              {searchQuery ? `No results found for "${searchQuery}"` : 'No connectors available under this filter.'}
            </p>
          </div>
          {(searchQuery || filterCategory !== 'all') && (
            <button
              onClick={() => {
                setSearchQuery('');
                setFilterCategory('all');
              }}
              className="px-4 py-2 rounded-xl border border-[#FF6D00]/40 bg-[#FF6D00]/10 hover:bg-[#FF6D00]/20 text-[#FF6D00] text-xs font-semibold transition"
            >
              Reset Filters
            </button>
          )}
        </div>
      ) : (
        /* ── Connector Grid ── */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {filteredProviders.map((prov) => {
            const conn = activeConnections.find(
              (c) =>
                c.provider.toLowerCase().includes(prov.id.toLowerCase()) ||
                prov.name.toLowerCase().includes(c.provider.toLowerCase())
            );
            const health = getHealthForProvider(prov.name);
            return (
              <OAuthCard
                key={prov.id}
                provider={prov}
                connection={conn}
                health={health}
                onDisconnect={disconnectProvider}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};
