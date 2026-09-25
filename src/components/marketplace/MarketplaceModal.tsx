import React, { useState, useEffect } from 'react';
import { Store, Search, Star, GitFork, Sparkles, X, Layers, Clock } from 'lucide-react';
import { apiClient } from '../../api/client';

export interface MarketplaceItem {
  id: string;
  title: string;
  description: string;
  purpose: string;
  connectors: string[];
  difficulty: string;
  estimated_runtime_ms: number;
  industry: string;
  use_cases: string[];
  author: string;
  version: string;
  rating: number;
  rating_count: number;
  fork_count: number;
  workflow_graph: any;
}

interface MarketplaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportWorkflow: (graph: any) => void;
}

export const MarketplaceModal: React.FC<MarketplaceModalProps> = ({
  isOpen,
  onClose,
  onImportWorkflow,
}) => {
  const [query, setQuery] = useState<string>('');
  const [templates, setTemplates] = useState<MarketplaceItem[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('All');

  useEffect(() => {
    if (isOpen) {
      fetchTemplates();
    }
  }, [isOpen]);

  const fetchTemplates = async () => {
    try {
      const resp = await apiClient.get('/marketplace/templates');
      setTemplates(resp.data || []);
    } catch {
      // Fallback seed
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) {
      fetchTemplates();
      return;
    }
    try {
      const resp = await apiClient.post('/marketplace/recommend', { query });
      setTemplates(resp.data || []);
    } catch {
      fetchTemplates();
    }
  };

  const handlePersonalizeAndImport = async (tplId: string) => {
    try {
      const resp = await apiClient.post('/marketplace/personalize', {
        template_id: tplId,
        user_context: { email: 'user@company.com', company: 'Company' },
      });
      onImportWorkflow(resp.data);
      onClose();
    } catch {
      alert('Personalization failed.');
    }
  };

  const handleFork = async (tplId: string) => {
    try {
      const resp = await apiClient.post('/marketplace/fork', { template_id: tplId });
      onImportWorkflow(resp.data.workflow_graph);
      onClose();
    } catch {
      alert('Fork failed.');
    }
  };

  if (!isOpen) return null;

  const industries = ['All', 'HR', 'Engineering', 'Finance', 'Marketing', 'E-Commerce'];

  const filteredTemplates = selectedIndustry === 'All'
    ? templates
    : templates.filter((t) => t.industry === selectedIndustry);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-4xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm">
              <Store className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">AI Workflow Marketplace</h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Discover, Personalize, and Fork AI Workflows</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search & Industry Filters */}
        <div className="p-6 pb-2 space-y-3 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search marketplace templates by prompt or connector... e.g. HR Onboarding"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI Search</span>
            </button>
          </div>

          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1">
            {industries.map((ind) => (
              <button
                key={ind}
                onClick={() => setSelectedIndustry(ind)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
                  selectedIndustry === ind
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                }`}
              >
                {ind}
              </button>
            ))}
          </div>
        </div>

        {/* Catalog */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          <div className="grid grid-cols-2 gap-4">
            {filteredTemplates.map((tpl) => (
              <div
                key={tpl.id}
                className="p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 rounded-xl flex flex-col justify-between space-y-3"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300">
                      {tpl.industry}
                    </span>
                    <div className="flex items-center space-x-1 text-xs text-amber-500 font-bold">
                      <Star className="w-3.5 h-3.5 fill-amber-400" />
                      <span>{tpl.rating}</span>
                      <span className="text-[10px] text-slate-400">({tpl.rating_count})</span>
                    </div>
                  </div>

                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">{tpl.title}</h4>
                  <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2">{tpl.description}</p>
                </div>

                <div className="pt-2 border-t border-slate-200 dark:border-slate-700/60 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2 text-[11px] text-slate-500">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{tpl.estimated_runtime_ms}ms</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Layers className="w-3 h-3" />
                      <span>{tpl.difficulty}</span>
                    </span>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <button
                      onClick={() => handleFork(tpl.id)}
                      className="p-1.5 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-700 dark:text-slate-200 rounded-lg text-xs transition"
                      title="Fork Workflow"
                    >
                      <GitFork className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handlePersonalizeAndImport(tpl.id)}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold transition flex items-center space-x-1"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>Personalize</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
