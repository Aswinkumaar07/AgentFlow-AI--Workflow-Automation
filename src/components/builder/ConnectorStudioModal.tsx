import React, { useState } from 'react';
import { Layers, X, CheckCircle2, Code2, Sparkles } from 'lucide-react';
import { apiClient } from '../../api/client';

export interface GeneratedConnector {
  provider: string;
  category: string;
  icon: string;
  description: string;
  authentication: string;
  capabilities: string[];
  operations: any[];
  generated_test_code: string;
}

interface ConnectorStudioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnectorRegistered?: (connector: GeneratedConnector) => void;
}

export const ConnectorStudioModal: React.FC<ConnectorStudioModalProps> = ({
  isOpen,
  onClose,
  onConnectorRegistered,
}) => {
  const [rawSpec, setRawSpec] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [generatedSpec, setGeneratedSpec] = useState<GeneratedConnector | null>(null);

  if (!isOpen) return null;

  const handleUploadAndGenerate = async () => {
    if (!rawSpec.trim()) return;
    setIsLoading(true);

    try {
      let parsed: any;
      try {
        parsed = JSON.parse(rawSpec);
      } catch {
        parsed = rawSpec;
      }

      const resp = await apiClient.post('/connector-studio/upload-spec', {
        spec: parsed,
      });

      const data: GeneratedConnector = resp.data;
      setGeneratedSpec(data);
      if (onConnectorRegistered) {
        onConnectorRegistered(data);
      }
    } catch (err: any) {
      alert('Failed to parse API specification. Please check format.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Zero-Code Connector Studio</h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Generate & Register Production Connectors Live</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {!generatedSpec ? (
            <div className="space-y-4">
              <div className="p-4 bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/50 rounded-xl text-xs text-indigo-800 dark:text-indigo-300">
                Paste any <strong>OpenAPI 3.x</strong>, <strong>Swagger 2.0</strong>, <strong>Postman Collection</strong>, or <strong>GraphQL</strong> spec JSON/YAML below. AI will automatically construct operations, parameters, authentication, and register it for live Planner V3 execution.
              </div>

              <textarea
                rows={10}
                placeholder='Paste raw JSON or OpenAPI specification here... e.g. {"openapi": "3.0.0", "info": {"title": "Twilio API"}, ...}'
                value={rawSpec}
                onChange={(e) => setRawSpec(e.target.value)}
                className="w-full p-4 font-mono text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/50 rounded-xl flex items-center space-x-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-500 shrink-0" />
                <div>
                  <h4 className="text-sm font-bold text-emerald-900 dark:text-emerald-200">
                    Connector '{generatedSpec.provider}' Registered Live!
                  </h4>
                  <p className="text-xs text-emerald-800 dark:text-emerald-300">
                    {generatedSpec.description} — Icon assigned: <span className="font-mono">{generatedSpec.icon}</span>
                  </p>
                </div>
              </div>

              {/* Generated Operations */}
              <div className="space-y-2">
                <h5 className="text-xs font-bold text-slate-900 dark:text-white uppercase">Generated Operations</h5>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {generatedSpec.operations.map((op, i) => (
                    <div key={i} className="p-2.5 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 rounded-lg text-xs flex items-center justify-between">
                      <span className="font-semibold text-slate-900 dark:text-white">{op.operation}</span>
                      <span className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400">{op.summary}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Generated Unit Test */}
              <div className="space-y-1">
                <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase flex items-center space-x-1">
                  <Code2 className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Generated Pytest Verification Suite</span>
                </div>
                <pre className="p-3 bg-slate-950 text-slate-200 text-[11px] font-mono rounded-xl border border-slate-800 overflow-x-auto">
                  {generatedSpec.generated_test_code}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-between">
          {!generatedSpec ? (
            <>
              <span className="text-xs text-slate-500 dark:text-slate-400">Zero manual connector coding required.</span>
              <button
                onClick={handleUploadAndGenerate}
                disabled={!rawSpec.trim() || isLoading}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-xl text-xs font-bold shadow-md transition flex items-center space-x-2"
              >
                <Sparkles className="w-4 h-4" />
                <span>{isLoading ? 'Generating Connector...' : 'Generate & Register Connector'}</span>
              </button>
            </>
          ) : (
            <button
              onClick={() => {
                setGeneratedSpec(null);
                setRawSpec('');
              }}
              className="px-4 py-2 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 text-slate-900 dark:text-white rounded-xl text-xs font-medium transition"
            >
              Upload Another Spec
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
