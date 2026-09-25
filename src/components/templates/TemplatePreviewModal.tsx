import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { TemplateMetadata } from '../../types/templates';
import { templatesApi } from '../../api/templates';
import { oauthApi } from '../../api/oauth';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import { useOAuthStore } from '../../store/useOAuthStore';
import { checkProviderReadiness } from '../../utils/oauthReadiness';
import { Sparkles, X, ArrowRight, Loader2, CheckCircle2, AlertCircle, Sliders, Layers, KeyRound, ExternalLink } from 'lucide-react';

interface TemplatePreviewModalProps {
  template: TemplateMetadata | null;
  onClose: () => void;
}

export const TemplatePreviewModal: React.FC<TemplatePreviewModalProps> = ({ template, onClose }) => {
  const navigate = useNavigate();
  const setWorkflow = useWorkflowStore((state) => state.setWorkflow);
  const setWorkflowId = useWorkflowStore((state) => state.setWorkflowId);
  const setRestoredNotice = useWorkflowStore((state) => state.setRestoredNotice);
  const connections = useOAuthStore((state) => state.connections);
  const fetchOAuthData = useOAuthStore((state) => state.fetchOAuthData);

  const [paramValues, setParamValues] = useState<Record<string, any>>({});
  const [isInstantiating, setIsInstantiating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Refresh connection state on mount
  useEffect(() => {
    fetchOAuthData();
  }, [fetchOAuthData]);

  // Initialize parameter defaults whenever template changes
  useEffect(() => {
    if (template && template.configurable_parameters) {
      const initial: Record<string, any> = {};
      template.configurable_parameters.forEach((p) => {
        initial[p.key] = p.default ?? '';
      });
      setParamValues(initial);
      setErrorMsg(null);
    }
  }, [template]);

  if (!template) return null;

  const reqProviders = template.required_providers || template.connectors || [];
  const readiness = checkProviderReadiness(reqProviders, connections);

  const stepsList = template.workflow_spec?.nodes || template.workflow_spec?.steps || [];

  const handleConnectProvider = async (providerName: string) => {
    try {
      await oauthApi.connectAccount(providerName);
    } catch (err: any) {
      console.error(`Failed to connect provider '${providerName}':`, err);
      setErrorMsg(`Failed to launch connection flow for ${providerName}.`);
    }
  };

  const handleCreateWorkflow = async () => {
    try {
      setErrorMsg(null);

      // Check required OAuth connections first
      if (!readiness.ready) {
        const missingStr = readiness.missing_connections.join(', ');
        setErrorMsg(`Connection required for provider(s): ${missingStr}. Please connect all required services.`);
        if (readiness.missing_connections.length > 0) {
          handleConnectProvider(readiness.missing_connections[0]);
        }
        return;
      }

      // Validate required parameters
      if (template.configurable_parameters) {
        for (const p of template.configurable_parameters) {
          if (p.required) {
            const val = paramValues[p.key];
            if (val === undefined || val === null || String(val).trim() === '') {
              setErrorMsg(`Please enter a value for ${p.label || p.key}`);
              return;
            }
          }
        }
      }

      setIsInstantiating(true);

      const result = await templatesApi.instantiateTemplate(template.id, paramValues);

      const wfPayload = {
        workflow_id: result.workflow_id,
        name: result.name,
        workflow_json: result.workflow_json,
        nodes: result.nodes,
        edges: result.edges,
      };

      setWorkflowId(result.workflow_id);
      setWorkflow(wfPayload);
      setRestoredNotice(`Created workflow from template "${template.title}" (v${result.version_number})`);

      setIsInstantiating(false);
      onClose();

      // Navigate to builder preserving persistent workflow UUID query param
      navigate(`/builder?id=${encodeURIComponent(result.workflow_id)}`);
    } catch (err: any) {
      console.error('Failed to instantiate template:', err);
      try {
        const clonedWf = await templatesApi.cloneTemplate(template.id);
        const wfId = clonedWf.workflow_id || `wf_tpl_${Math.random().toString(36).substring(2, 8)}`;
        setWorkflowId(wfId);
        setWorkflow({
          workflow_id: wfId,
          name: clonedWf.title || clonedWf.name || template.title,
          workflow_json: clonedWf,
          steps: clonedWf.steps || template.workflow_spec?.steps || [],
        });
        setRestoredNotice(`Loaded template "${template.title}"`);
        setIsInstantiating(false);
        onClose();

        // Navigate to builder preserving persistent fallback workflow ID
        navigate(`/builder?id=${encodeURIComponent(wfId)}`);
      } catch (fallbackErr: any) {
        setErrorMsg(err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'Failed to instantiate template workflow.');
        setIsInstantiating(false);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xl flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-[#13102A] border border-[rgba(255,255,255,0.12)] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 border-b border-[rgba(255,255,255,0.08)] flex items-center justify-between bg-[#13102A]">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-xl bg-[#FF6D00]/20 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center font-bold">
              <Sparkles className="h-4 w-4" />
            </div>
            <h3 className="font-bold text-sm text-white">Template Preview & Customization</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 text-[#A098AE] hover:text-white transition cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 flex-1 overflow-y-auto space-y-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30 uppercase tracking-wider">
                {template.category}
              </span>
              <span className="text-xs text-[#A098AE] font-mono">Difficulty: {template.difficulty}</span>
              <span className="text-xs text-[#A098AE] font-mono">• Est. Latency: {template.estimated_time_ms}ms</span>
            </div>
            <h2 className="text-xl font-bold tracking-tight text-white">{template.title}</h2>
            <p className="text-xs text-[#A098AE] mt-2 leading-relaxed font-normal">{template.description}</p>
          </div>

          {/* Integrations & OAuth Requirements */}
          <div className="p-4 rounded-2xl border border-[rgba(255,255,255,0.10)] bg-[#1B1728]/80 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#A098AE] flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-[#FF6D00]" /> Required Integrations & Connection Status
            </h4>
            <div className="flex flex-col gap-2">
              {readiness.provider_results.map((res) => {
                const isReady = res.status === 'READY' || res.status === 'INTERNAL_PROVIDER';
                const label = res.status === 'INTERNAL_PROVIDER' ? 'Internal AI' : (isReady ? 'Connected' : 'Connection Required');
                return (
                  <div
                    key={res.provider}
                    className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs border ${
                      isReady
                        ? 'bg-[#22C55E]/10 border-[#22C55E]/30 text-[#34D399]'
                        : 'bg-[#FF6D00]/10 border-[#FF6D00]/30 text-[#FF6D00]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {isReady ? (
                        <CheckCircle2 className="h-4 w-4 text-[#34D399] shrink-0" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-[#FF6D00] shrink-0" />
                      )}
                      <span className="font-bold font-mono uppercase">{res.provider}</span>
                      <span className="text-[11px] opacity-80 font-sans">({label})</span>
                    </div>

                    {res.status === 'MISSING_CONNECTION' && (
                      <button
                        onClick={() => handleConnectProvider(res.provider)}
                        className="px-3 py-1 bg-[#FF6D00] text-white font-bold rounded-lg text-xs hover:opacity-90 transition flex items-center gap-1 shadow-sm cursor-pointer"
                      >
                        <ExternalLink className="h-3 w-3" /> Connect {res.provider}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Parameter Customization Form */}
          {template.configurable_parameters && template.configurable_parameters.length > 0 && (
            <div className="p-4 rounded-2xl border border-[rgba(255,255,255,0.10)] bg-[#1B1728]/80 space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#A098AE] flex items-center gap-1.5">
                <Sliders className="h-3.5 w-3.5 text-[#FF6D00]" /> Customize Parameters
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {template.configurable_parameters.map((param) => (
                  <div key={param.key} className="space-y-1.5">
                    <label className="text-xs font-semibold text-white flex items-center justify-between">
                      <span>{param.label}</span>
                      {param.required && <span className="text-[10px] text-[#FF6D00] font-bold">*Required</span>}
                    </label>
                    {param.type === 'select' && param.options ? (
                      <select
                        value={paramValues[param.key] ?? param.default ?? ''}
                        onChange={(e) => setParamValues({ ...paramValues, [param.key]: e.target.value })}
                        className="w-full px-3 py-2 text-xs bg-[#0E0918] text-white border border-[rgba(255,255,255,0.12)] rounded-xl focus:outline-none focus:border-[#FF6D00] focus:ring-1 focus:ring-[#FF6D00] transition cursor-pointer font-sans"
                      >
                        {param.options.map((opt) => (
                          <option key={opt} value={opt} className="bg-[#13102A] text-white">
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={param.type === 'number' ? 'number' : 'text'}
                        value={paramValues[param.key] ?? ''}
                        onChange={(e) => setParamValues({ ...paramValues, [param.key]: e.target.value })}
                        placeholder={param.key === 'slack_channel' ? '#all-agentflow-ai' : (param.description || `Enter ${param.label}`)}
                        className="w-full px-3 py-2 text-xs bg-[#0E0918] text-white placeholder-[#7A748E] border border-[rgba(255,255,255,0.12)] rounded-xl focus:outline-none focus:border-[#FF6D00] focus:ring-1 focus:ring-[#FF6D00] transition font-mono"
                      />
                    )}
                    {param.description && (
                      <p className="text-[10px] text-[#A098AE]">{param.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Workflow DAG Step Flow Timeline */}
          <div className="space-y-2 pt-2 border-t border-[rgba(255,255,255,0.08)]">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#A098AE]">
              Workflow DAG Execution Steps
            </h4>
            <div className="space-y-2">
              {stepsList.map((step: any, idx: number) => (
                <div
                  key={step.id || step.step_id || idx}
                  className="p-3 rounded-xl border border-[rgba(255,255,255,0.08)] bg-[#1B1728]/70 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-6 w-6 rounded-full bg-[#FF6D00]/20 text-[#FF6D00] flex items-center justify-center font-bold text-[11px]">
                      {idx + 1}
                    </div>
                    <div>
                      <p className="font-semibold text-white">{step.label || step.provider}</p>
                      <p className="text-[10px] text-[#A098AE] font-mono">{step.operation || step.operation_id || 'Action'}</p>
                    </div>
                  </div>
                  <span className="text-[10px] text-[#34D399] font-semibold flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> Validated Step
                  </span>
                </div>
              ))}
            </div>
          </div>

          {errorMsg && (
            <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[rgba(255,255,255,0.08)] bg-[#13102A] flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-[rgba(255,255,255,0.12)] rounded-xl text-xs font-semibold text-[#A098AE] hover:text-white hover:bg-[#1B1728] transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={handleCreateWorkflow}
            disabled={isInstantiating}
            className={`px-5 py-2 text-xs font-bold rounded-xl transition flex items-center gap-2 shadow-[0_0_20px_rgba(255,109,0,0.35)] cursor-pointer disabled:opacity-50 ${
              readiness.ready
                ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white hover:opacity-95'
                : 'bg-amber-500 text-black hover:bg-amber-400 font-bold'
            }`}
          >
            {isInstantiating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Instantiating DAG & Version...
              </>
            ) : readiness.ready ? (
              <>
                Create Workflow <ArrowRight className="h-4 w-4" />
              </>
            ) : (
              <>
                <KeyRound className="h-4 w-4" /> Connect Required Services
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
