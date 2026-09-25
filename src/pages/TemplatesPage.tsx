import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { templatesApi } from '../api/templates';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { TemplateCard } from '../components/templates/TemplateCard';
import { TemplatePreviewModal } from '../components/templates/TemplatePreviewModal';
import type { TemplateMetadata } from '../types/templates';
import { LayoutTemplate, Search, PackageOpen, X, RotateCw, AlertCircle } from 'lucide-react';

export const TemplatesPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [search, setSearch] = useState('');
  const [previewTemplate, setPreviewTemplate] = useState<TemplateMetadata | null>(null);

  const {
    data: templates = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['templates', selectedCategory, search],
    queryFn: () => templatesApi.getTemplates(selectedCategory, search),
  });

  const categories = [
    'All',
    'Email',
    'Communication',
    'Productivity',
    'Reports',
    'Scheduled Automation',
    'Multi-Service',
    'Finance & Invoicing',
  ];

  const safeTemplates = Array.isArray(templates) ? templates : [];

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-[1440px] mx-auto pb-12">
        {/* ── 1. PAGE HEADER ─────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.12)] shadow-xl">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center font-bold shadow-[0_0_15px_rgba(255,109,0,0.20)]">
              <LayoutTemplate className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl font-bold tracking-tight text-white">Templates</h1>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30">
                  {safeTemplates.length} Available
                </span>
              </div>
              <p className="text-xs text-[#A098AE] mt-1 font-medium">
                Browse pre-built, enterprise-validated automation workflows for instant deployment.
              </p>
            </div>
          </div>

          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="px-3.5 py-2.5 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[#1B1728] hover:bg-[#231E3A] text-xs font-semibold text-[#A098AE] hover:text-white transition flex items-center gap-2 cursor-pointer self-start sm:self-auto"
            title="Refresh Catalog"
          >
            <RotateCw className={`h-3.5 w-3.5 text-[#FF6D00] ${isLoading ? 'animate-spin' : ''}`} />
            <span>Sync Catalog</span>
          </button>
        </div>

        {/* ── 2. SEARCH & CATEGORY FILTERS BAR ───────────────────────────── */}
        <div className="p-4 rounded-2xl bg-[#13102A]/70 backdrop-blur-xl border border-[rgba(255,255,255,0.10)] flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between shadow-lg">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#7A748E]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search templates by connector, name, or keyword..."
              className="w-full pl-10 pr-8 py-2 text-xs bg-[#0E0918] text-white placeholder-[#7A748E] rounded-xl border border-[rgba(255,255,255,0.12)] focus:outline-none focus:border-[#FF6D00] focus:ring-1 focus:ring-[#FF6D00] transition shadow-inner font-sans"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 rounded hover:bg-white/10 text-[#A098AE] transition cursor-pointer"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>

          {/* Category Filter Pills */}
          <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                  selectedCategory === cat
                    ? 'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-[0_0_10px_rgba(255,109,0,0.30)]'
                    : 'bg-[#0E0918] border border-[rgba(255,255,255,0.12)] text-[#A098AE] hover:text-white hover:border-[#FF6D00]/30'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* ── 3. LOADING SKELETONS ─────────────────────────────────────── */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3, 4, 5, 6].map((idx) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] space-y-4 animate-pulse h-56"
              >
                <div className="flex items-center justify-between">
                  <div className="h-5 w-24 rounded-full bg-[#1B1728]" />
                  <div className="h-5 w-16 rounded-full bg-[#1B1728]" />
                </div>
                <div className="space-y-2">
                  <div className="h-4 w-3/4 rounded bg-[#1B1728]" />
                  <div className="h-3 w-1/2 rounded bg-[#1B1728]" />
                </div>
                <div className="pt-3 border-t border-[rgba(255,255,255,0.06)] flex justify-between">
                  <div className="h-3 w-20 rounded bg-[#1B1728]" />
                  <div className="h-7 w-28 rounded-xl bg-[#1B1728]" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── 4. ERROR STATE ───────────────────────────────────────────── */}
        {isError && !isLoading && (
          <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 flex flex-col items-center justify-center text-center space-y-3 my-4">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <div>
              <h3 className="text-sm font-bold text-white">Unable to load templates</h3>
              <p className="text-xs text-red-300 mt-1 font-mono">
                {error instanceof Error ? error.message : 'Backend templates service unreachable.'}
              </p>
            </div>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 text-xs font-bold rounded-xl transition flex items-center gap-1.5 cursor-pointer"
            >
              <RotateCw className="h-3.5 w-3.5" /> Retry Catalog Load
            </button>
          </div>
        )}

        {/* ── 5. EMPTY STATE ───────────────────────────────────────────── */}
        {!isLoading && !isError && safeTemplates.length === 0 && (
          <div className="p-12 text-center rounded-2xl bg-[#13102A]/80 backdrop-blur-2xl border border-[rgba(255,255,255,0.12)] shadow-xl max-w-lg mx-auto space-y-4 my-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center mx-auto shadow-[0_0_20px_rgba(255,109,0,0.20)]">
              <PackageOpen className="h-8 w-8" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">No Workflow Templates Found</h3>
              <p className="text-xs text-[#A098AE] mt-1 leading-relaxed">
                No matching workflow templates found for &quot;{search || selectedCategory}&quot;. Try adjusting your search query or category filter.
              </p>
            </div>
            <button
              onClick={() => {
                setSearch('');
                setSelectedCategory('All');
              }}
              className="px-5 py-2.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl hover:opacity-95 transition inline-flex items-center gap-2 shadow-[0_0_20px_rgba(255,109,0,0.35)] cursor-pointer"
            >
              Clear Filters
            </button>
          </div>
        )}

        {/* ── 6. TEMPLATE GRID CATALOG ──────────────────────────────────── */}
        {!isLoading && !isError && safeTemplates.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {safeTemplates.map((tpl) => (
              <TemplateCard key={tpl.id} template={tpl} onPreview={setPreviewTemplate} />
            ))}
          </div>
        )}
      </div>

      <TemplatePreviewModal template={previewTemplate} onClose={() => setPreviewTemplate(null)} />
    </DashboardLayout>
  );
};
