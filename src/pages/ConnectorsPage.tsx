import React, { useEffect, useState, useMemo } from 'react';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { ConnectorsHeader } from '../components/connectors/ConnectorsHeader';
import { ConnectorCard } from '../components/connectors/ConnectorCard';
import { ConnectorSchemaModal } from '../components/connectors/ConnectorSchemaModal';
import { useOAuthStore } from '../store/useOAuthStore';
import { connectorsApi, type ConnectorMetadata } from '../api/connectors';
import type { OAuthProvider } from '../types/oauth';
import { Loader2, ShieldCheck, RefreshCw, Cpu } from 'lucide-react';

export const ConnectorsPage: React.FC = () => {
  const {
    providers,
    connections,
    healthStatus,
    isLoading,
    fetchOAuthData,
    getHealthForProvider,
  } = useOAuthStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<'all' | 'connected' | 'attention' | 'oauth2'>('all');
  const [connectorDefsMap, setConnectorDefsMap] = useState<Record<string, ConnectorMetadata>>({});
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalProvider, setModalProvider] = useState<OAuthProvider | null>(null);
  const [modalConnectorDef, setModalConnectorDef] = useState<ConnectorMetadata | null>(null);
  const [isModalLoading, setIsModalLoading] = useState(false);

  useEffect(() => {
    fetchOAuthData();

    // Fetch connector metadata schemas
    connectorsApi.listConnectors().then((defs) => {
      if (Array.isArray(defs)) {
        const map: Record<string, ConnectorMetadata> = {};
        defs.forEach((d) => {
          if (d && d.provider) {
            map[d.provider.toLowerCase()] = d;
          }
        });
        setConnectorDefsMap(map);
      }
    });
  }, [fetchOAuthData]);

  // Derived telemetry metrics
  const totalProviders = providers.length;

  const connectedCount = useMemo(() => {
    return connections.filter((c) => c.status === 'CONNECTED').length;
  }, [connections]);

  const attentionCount = useMemo(() => {
    return healthStatus.filter(
      (h) => h.status === 'expired' || h.status === 'expiring_soon'
    ).length;
  }, [healthStatus]);

  const totalOperationsCount = useMemo(() => {
    let count = 0;
    Object.values(connectorDefsMap).forEach((def) => {
      if (def.supported_operations) {
        count += def.supported_operations.length;
      } else if (def.operation_schemas) {
        count += Object.keys(def.operation_schemas).length;
      }
    });
    return count;
  }, [connectorDefsMap]);

  // Filtered providers list
  const filteredProviders = useMemo(() => {
    const query = (searchQuery || '').toLowerCase().trim();

    return providers.filter((p) => {
      if (!p) return false;

      const pName = (p.name || '').toLowerCase();
      const pAuthType = (p.auth_type || '').toLowerCase();

      // Search Query filter
      const matchesSearch =
        query === '' ||
        pName.includes(query) ||
        pAuthType.includes(query);

      if (!matchesSearch) return false;

      // Category filter
      const conn = connections.find(
        (c) => (c?.provider || '').toLowerCase() === pName
      );
      const isConnected = conn && conn.status === 'CONNECTED';
      const health = p.name ? getHealthForProvider(p.name) : undefined;

      if (filterCategory === 'connected') {
        return isConnected;
      }

      if (filterCategory === 'attention') {
        const needsAttention =
          health?.status === 'expired' ||
          health?.status === 'expiring_soon' ||
          !isConnected;
        return needsAttention;
      }

      if (filterCategory === 'oauth2') {
        return pAuthType.includes('oauth');
      }

      return true;
    });
  }, [providers, connections, healthStatus, searchQuery, filterCategory, getHealthForProvider]);

  // Open Schema Modal Handler
  const handleOpenSchemaModal = async (
    provider: OAuthProvider,
    def?: ConnectorMetadata | null
  ) => {
    setModalProvider(provider);
    setIsModalOpen(true);

    const existingDef = def || connectorDefsMap[provider.name.toLowerCase()];
    if (existingDef) {
      setModalConnectorDef(existingDef);
      setIsModalLoading(false);
    } else {
      setIsModalLoading(true);
      setModalConnectorDef(null);
      const fetchedDef = await connectorsApi.getConnectorDefinition(provider.name);
      setModalConnectorDef(fetchedDef);
      if (fetchedDef) {
        setConnectorDefsMap((prev) => ({
          ...prev,
          [provider.name.toLowerCase()]: fetchedDef,
        }));
      }
      setIsModalLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-200">
        {/* Header Telemetry & Controls */}
        <ConnectorsHeader
          totalProviders={totalProviders}
          connectedCount={connectedCount}
          attentionCount={attentionCount}
          totalOperationsCount={totalOperationsCount}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          activeFilter={filterCategory}
          onFilterChange={setFilterCategory}
          onRefresh={() => fetchOAuthData()}
          isRefreshing={isLoading}
        />

        {/* Content Section */}
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-4">
            <Loader2 className="h-10 w-10 text-[#FF6D00] animate-spin" />
            <p className="text-sm text-[rgba(255,255,255,0.6)] font-medium">
              Synchronizing enterprise connector integrations…
            </p>
          </div>
        ) : filteredProviders.length === 0 ? (
          <div className="py-16 px-6 rounded-2xl bg-[#13102A]/60 border border-[rgba(255,255,255,0.08)] backdrop-blur-md text-center space-y-3">
            <div className="h-12 w-12 rounded-2xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.4)] flex items-center justify-center mx-auto">
              <Cpu className="h-6 w-6" />
            </div>
            <h3 className="font-bold text-base text-white">No connectors found</h3>
            <p className="text-xs text-[rgba(255,255,255,0.5)] max-w-md mx-auto">
              No integrations match your search criteria "{searchQuery}" under the "{filterCategory}" filter.
            </p>
            <button
              onClick={() => {
                setSearchQuery('');
                setFilterCategory('all');
              }}
              className="mt-2 px-4 py-2 rounded-xl bg-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.15)] text-white text-xs font-semibold transition"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProviders.map((prov) => {
              const provName = (prov?.name || '').toLowerCase();
              const conn = connections.find(
                (c) => (c?.provider || '').toLowerCase() === provName
              );
              const health = prov?.name ? getHealthForProvider(prov.name) : undefined;
              const def = connectorDefsMap[provName];

              return (
                <ConnectorCard
                  key={prov.name}
                  provider={prov}
                  connection={conn}
                  health={health}
                  connectorDef={def}
                  onOpenSchemaModal={handleOpenSchemaModal}
                />
              );
            })}
          </div>
        )}

        {/* Security & Infrastructure Footer Callout */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-[#13102A]/90 via-[#1B1728]/80 to-[#13102A]/90 border border-[rgba(255,255,255,0.08)] backdrop-blur-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-2xl bg-[#FF6D00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center shrink-0">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-white flex items-center gap-2">
                <span>Enterprise OAuth 2.0 Security & Encryption</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 font-bold">
                  AES-256 GCM
                </span>
              </h4>
              <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5">
                All OAuth refresh tokens and API credentials are key-wrapped using hardware security module (HSM) level encryption with automated token lifecycle management.
              </p>
            </div>
          </div>
          <button
            onClick={() => fetchOAuthData()}
            className="px-4 py-2 rounded-xl bg-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.12)] border border-[rgba(255,255,255,0.1)] text-white text-xs font-semibold transition shrink-0 flex items-center gap-2"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Sync Integrations</span>
          </button>
        </div>

        {/* Schema Modal */}
        <ConnectorSchemaModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          providerName={modalProvider?.name ?? ''}
          connectorDef={modalConnectorDef}
          isLoading={isModalLoading}
        />
      </div>
    </DashboardLayout>
  );
};
