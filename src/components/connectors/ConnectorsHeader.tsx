import React from 'react';
import {
  Cpu,
  ShieldCheck,
  Search,
  CheckCircle2,
  AlertTriangle,
  Layers,
  RefreshCw,
} from 'lucide-react';

export type FilterCategory = 'all' | 'connected' | 'attention' | 'oauth2';

interface ConnectorsHeaderProps {
  totalProviders: number;
  connectedCount: number;
  attentionCount: number;
  totalOperationsCount: number;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  activeFilter: FilterCategory;
  onFilterChange: (cat: FilterCategory) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const ConnectorsHeader: React.FC<ConnectorsHeaderProps> = ({
  totalProviders,
  connectedCount,
  attentionCount,
  totalOperationsCount,
  searchQuery,
  onSearchChange,
  activeFilter,
  onFilterChange,
  onRefresh,
  isRefreshing,
}) => {
  const filterOptions: { id: FilterCategory; label: string }[] = [
    { id: 'all', label: 'All Providers' },
    { id: 'connected', label: 'Connected' },
    { id: 'attention', label: 'Attention Required' },
    { id: 'oauth2', label: 'OAuth 2.0' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 sm:p-8 rounded-3xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/80 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.36)] flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-[#FF6D00]/15 to-[#FF0C00]/5 blur-3xl pointer-events-none rounded-full" />

        <div className="flex items-center gap-4 relative z-10">
          <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] flex items-center justify-center text-white shadow-[0_4px_20px_rgba(255,109,0,0.4)] shrink-0">
            <Cpu className="h-7 w-7" />
          </div>

          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-extrabold text-white tracking-tight">Connectors & Integrations</h1>
              <span className="px-2.5 py-0.5 rounded-full bg-[#22C55E]/15 border border-[#22C55E]/30 text-[#22C55E] text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" /> AES-256 Vault
              </span>
            </div>
            <p className="text-sm text-[rgba(255,255,255,0.65)] mt-1">
              Connect AgentFlow AI to the services your workflows use.
            </p>
          </div>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="relative z-10 self-start md:self-auto px-4 py-2.5 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-white text-xs font-semibold flex items-center gap-2 transition-all duration-200 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 text-[#FF6D00] ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Connections</span>
        </button>
      </div>

      {/* Real Summary Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[#13102A]/60 backdrop-blur-md">
          <div className="flex items-center justify-between text-[#A098AE] text-xs font-medium">
            <span>Total Providers</span>
            <Cpu className="h-4 w-4 text-[#A098AE]" />
          </div>
          <p className="text-2xl font-extrabold text-white mt-1">{totalProviders}</p>
        </div>

        <div className="p-4 rounded-2xl border border-[#22C55E]/20 bg-[#22C55E]/5 backdrop-blur-md">
          <div className="flex items-center justify-between text-[#22C55E] text-xs font-medium">
            <span>Connected</span>
            <CheckCircle2 className="h-4 w-4 text-[#22C55E]" />
          </div>
          <p className="text-2xl font-extrabold text-[#22C55E] mt-1">{connectedCount}</p>
        </div>

        <div className="p-4 rounded-2xl border border-[#F59E0B]/20 bg-[#F59E0B]/5 backdrop-blur-md">
          <div className="flex items-center justify-between text-[#F59E0B] text-xs font-medium">
            <span>Attention Required</span>
            <AlertTriangle className="h-4 w-4 text-[#F59E0B]" />
          </div>
          <p className="text-2xl font-extrabold text-[#F59E0B] mt-1">{attentionCount}</p>
        </div>

        <div className="p-4 rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[#13102A]/60 backdrop-blur-md">
          <div className="flex items-center justify-between text-[#A098AE] text-xs font-medium">
            <span>Available Operations</span>
            <Layers className="h-4 w-4 text-[#FF6D00]" />
          </div>
          <p className="text-2xl font-extrabold text-white mt-1">{totalOperationsCount}</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 p-2 rounded-2xl bg-[#13102A]/60 border border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center gap-1.5 overflow-x-auto p-1 scrollbar-none">
          {filterOptions.map((opt) => (
            <button
              key={opt.id}
              onClick={() => onFilterChange(opt.id)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-200 ${
                activeFilter === opt.id
                  ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-[0_0_12px_rgba(255,109,0,0.3)]'
                  : 'text-[#A098AE] hover:text-white hover:bg-[#1B1728]'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72 px-1">
          <Search className="h-4 w-4 absolute left-4 top-1/2 -translate-y-1/2 text-[#A098AE]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search provider or scope..."
            className="w-full pl-10 pr-4 py-2 bg-[#1B1728] border border-[rgba(255,255,255,0.10)] rounded-xl text-xs text-white placeholder-[#A098AE] focus:outline-none focus:border-[#FF6D00] transition-colors"
          />
        </div>
      </div>
    </div>
  );
};
