import React from 'react';
import type { TemplateMetadata } from '../../types/templates';
import { useOAuthStore } from '../../store/useOAuthStore';
import { Sparkles, Clock, ArrowRight, Cpu, Layers, CheckCircle2, AlertCircle } from 'lucide-react';

interface TemplateCardProps {
  template: TemplateMetadata;
  onPreview: (template: TemplateMetadata) => void;
}

const OAUTH_PROVIDERS = new Set(['gmail', 'google', 'google_gmail', 'slack', 'github', 'stripe', 'notion', 'google_drive', 'drive', 'google_sheets', 'sheets']);

export const TemplateCard: React.FC<TemplateCardProps> = ({ template, onPreview }) => {
  const connections = useOAuthStore((state) => state.connections);

  const reqProviders = template.required_providers || template.connectors || [];

  const getProviderStatus = (prov: string) => {
    const norm = prov.toLowerCase();
    if (!OAUTH_PROVIDERS.has(norm)) {
      return { status: 'CONNECTED', label: 'Internal AI' };
    }
    const isConn = connections.some(
      (c) => c.status === 'CONNECTED' && (c.provider.toLowerCase() === norm || norm.includes(c.provider.toLowerCase()))
    );
    return isConn
      ? { status: 'CONNECTED', label: 'Connected' }
      : { status: 'REQUIRES_CONNECTION', label: 'Connection Required' };
  };

  return (
    <div className="rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.12)] p-5 shadow-xl hover:border-[#FF6D00]/40 hover:shadow-[0_0_20px_rgba(255,109,0,0.18)] transition-all duration-200 flex flex-col justify-between space-y-4 group">
      <div>
        {/* Header Badges */}
        <div className="flex items-center justify-between mb-3">
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30 uppercase tracking-wider">
            {template.category}
          </span>

          {template.featured && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
              <Sparkles className="h-3 w-3" /> Featured
            </span>
          )}
        </div>

        <h3 className="font-bold text-base text-white tracking-tight group-hover:text-[#FF6D00] transition line-clamp-1">
          {template.title}
        </h3>
        <p className="text-xs text-[#A098AE] mt-1.5 line-clamp-2 leading-relaxed">
          {template.description}
        </p>

        {/* Connector & OAuth Status Chips */}
        <div className="mt-4 pt-3 border-t border-[rgba(255,255,255,0.08)] space-y-1.5">
          <div className="flex items-center gap-1.5 flex-wrap">
            <Cpu className="h-3.5 w-3.5 text-[#FF6D00] mr-0.5" />
            {reqProviders.map((prov) => {
              const info = getProviderStatus(prov);
              const isConnected = info.status === 'CONNECTED';
              return (
                <span
                  key={prov}
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                    isConnected
                      ? 'bg-[#22C55E]/15 border-[#22C55E]/30 text-[#34D399]'
                      : 'bg-[#FF6D00]/15 border-[#FF6D00]/30 text-[#FF6D00]'
                  }`}
                  title={`${prov}: ${info.label}`}
                >
                  {isConnected ? (
                    <CheckCircle2 className="h-2.5 w-2.5 text-[#34D399]" />
                  ) : (
                    <AlertCircle className="h-2.5 w-2.5 text-[#FF6D00]" />
                  )}
                  {prov}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="pt-3 border-t border-[rgba(255,255,255,0.08)] flex items-center justify-between text-xs">
        <div className="flex items-center gap-3 text-[10px] text-[#A098AE] font-mono">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3 text-[#FF6D00]" /> {template.estimated_time_ms}ms
          </span>
          <span className="flex items-center gap-1">
            <Layers className="h-3 w-3 text-[#FF6D00]" /> {template.difficulty}
          </span>
        </div>

        <button
          onClick={() => onPreview(template)}
          className="px-4 py-2 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl hover:opacity-95 active:scale-[0.96] transition flex items-center gap-1.5 shadow-[0_0_15px_rgba(255,109,0,0.30)] cursor-pointer"
        >
          Use Template <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
};
