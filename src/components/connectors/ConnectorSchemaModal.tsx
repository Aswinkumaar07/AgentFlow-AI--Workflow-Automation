import React, { useEffect, useState } from 'react';
import type { ConnectorMetadata, OperationSchema } from '../../api/connectors';
import {
  X,
  ExternalLink,
  Layers,
  Cpu,
  Info,
} from 'lucide-react';

interface ConnectorSchemaModalProps {
  isOpen: boolean;
  onClose: () => void;
  providerName: string;
  connectorDef: ConnectorMetadata | null;
  isLoading: boolean;
}

export const ConnectorSchemaModal: React.FC<ConnectorSchemaModalProps> = ({
  isOpen,
  onClose,
  providerName,
  connectorDef,
  isLoading,
}) => {
  const [selectedOperationId, setSelectedOperationId] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const supportedOps = connectorDef?.supported_operations || [];
  const schemasMap = connectorDef?.operation_schemas || {};

  const activeOpId = selectedOperationId || supportedOps[0] || null;
  const activeSchema: OperationSchema | undefined = activeOpId ? schemasMap[activeOpId] : undefined;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-[#13102A] border border-[rgba(255,255,255,0.12)] rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Modal Header */}
        <div className="p-6 border-b border-[rgba(255,255,255,0.08)] bg-[#1B1728]/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 flex items-center justify-center text-[#FF6D00]">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white tracking-tight">
                  {connectorDef?.display_name || providerName} Schema
                </h3>
                {connectorDef?.version && (
                  <span className="px-2 py-0.5 rounded-full bg-[#1B1728] border border-[rgba(255,255,255,0.1)] text-[10px] font-mono text-[#A098AE]">
                    v{connectorDef.version}
                  </span>
                )}
              </div>
              <p className="text-xs text-[rgba(255,255,255,0.6)]">
                Supported operations and parameter schemas
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {connectorDef?.documentation_url && (
              <a
                href={connectorDef.documentation_url}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 rounded-lg border border-[rgba(255,255,255,0.10)] bg-[#1B1728] hover:bg-[#231E3A] text-xs font-semibold text-[#A098AE] hover:text-white flex items-center gap-1.5 transition-colors"
              >
                <span>Docs</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
            <button
              onClick={onClose}
              aria-label="Close modal"
              className="p-2 rounded-xl text-[#A098AE] hover:text-white hover:bg-[#1B1728] transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
              <div className="h-8 w-8 rounded-full border-2 border-[#FF6D00] border-t-transparent animate-spin" />
              <p className="text-xs text-[#A098AE]">Loading operation schema definitions...</p>
            </div>
          ) : supportedOps.length === 0 ? (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
              <Info className="h-8 w-8 text-[#A098AE]" />
              <p className="text-sm font-semibold text-white">No operation schema is available for this connector.</p>
              <p className="text-xs text-[#A098AE] max-w-sm">
                This service connector does not currently publish operation parameter definitions via the API.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Operations Selector Column */}
              <div className="space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#A098AE]">
                  Operations ({supportedOps.length})
                </span>
                <div className="space-y-1.5">
                  {supportedOps.map((opId) => {
                    const isSelected = opId === activeOpId;
                    const schema = schemasMap[opId];
                    return (
                      <button
                        key={opId}
                        onClick={() => setSelectedOperationId(opId)}
                        className={`w-full text-left p-3 rounded-xl border text-xs font-semibold transition-all duration-150 flex items-center justify-between ${
                          isSelected
                            ? 'bg-[#FF6D00]/15 border-[#FF6D00]/40 text-white shadow-[0_0_12px_rgba(255,109,0,0.15)]'
                            : 'bg-[#1B1728]/60 border-[rgba(255,255,255,0.08)] text-[#A098AE] hover:text-white hover:bg-[#1B1728]'
                        }`}
                      >
                        <span className="truncate">{schema?.display_name || opId}</span>
                        <Layers className="h-3.5 w-3.5 shrink-0 opacity-60" />
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Operation Details Column */}
              <div className="md:col-span-2 space-y-4 bg-[#1B1728]/40 border border-[rgba(255,255,255,0.08)] rounded-2xl p-4">
                {activeOpId ? (
                  <>
                    <div className="border-b border-[rgba(255,255,255,0.08)] pb-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-bold text-white">
                          {activeSchema?.display_name || activeOpId}
                        </h4>
                        <span className="px-2 py-0.5 rounded bg-[#0E0918] border border-[rgba(255,255,255,0.1)] text-[10px] font-mono text-[#FF6D00]">
                          {activeOpId}
                        </span>
                      </div>
                      {activeSchema?.description && (
                        <p className="text-xs text-[#A098AE] mt-1">{activeSchema.description}</p>
                      )}
                    </div>

                    {/* Parameters Schema List */}
                    {activeSchema && (
                      <div className="space-y-4">
                        {activeSchema.required_parameters && activeSchema.required_parameters.length > 0 && (
                          <div className="space-y-2">
                            <span className="text-[11px] font-bold text-[#FF6D00] uppercase tracking-wider">
                              Required Parameters ({activeSchema.required_parameters.length})
                            </span>
                            <div className="space-y-2">
                              {activeSchema.required_parameters.map((param) => (
                                <div
                                  key={param.name}
                                  className="p-3 rounded-xl bg-[#0E0918] border border-[rgba(255,255,255,0.08)] space-y-1"
                                >
                                  <div className="flex items-center justify-between">
                                    <span className="text-xs font-bold text-white font-mono">{param.name}</span>
                                    <span className="px-1.5 py-0.5 rounded bg-[#FF6D00]/15 text-[#FF6D00] text-[10px] font-mono">
                                      {param.type}
                                    </span>
                                  </div>
                                  <p className="text-[11px] text-[#A098AE]">{param.display_name || param.description}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {activeSchema.optional_parameters && activeSchema.optional_parameters.length > 0 && (
                          <div className="space-y-2">
                            <span className="text-[11px] font-bold text-[#A098AE] uppercase tracking-wider">
                              Optional Parameters ({activeSchema.optional_parameters.length})
                            </span>
                            <div className="space-y-2">
                              {activeSchema.optional_parameters.map((param) => (
                                <div
                                  key={param.name}
                                  className="p-3 rounded-xl bg-[#0E0918] border border-[rgba(255,255,255,0.06)] space-y-1 opacity-80"
                                >
                                  <div className="flex items-center justify-between">
                                    <span className="text-xs font-semibold text-[#A098AE] font-mono">{param.name}</span>
                                    <span className="px-1.5 py-0.5 rounded bg-[#1B1728] text-[#A098AE] text-[10px] font-mono">
                                      {param.type}
                                    </span>
                                  </div>
                                  {param.description && (
                                    <p className="text-[11px] text-[#A098AE]">{param.description}</p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-xs text-[#A098AE]">Select an operation to view parameter details.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
