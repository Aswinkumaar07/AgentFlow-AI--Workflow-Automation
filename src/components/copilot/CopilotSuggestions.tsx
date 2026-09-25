import React from 'react';
import { Sparkles } from 'lucide-react';

interface SuggestionsProps {
  suggestions: string[];
  onSelectSuggestion: (text: string) => void;
}

export const CopilotSuggestions: React.FC<SuggestionsProps> = ({
  suggestions,
  onSelectSuggestion,
}) => {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 py-2 px-4 bg-slate-50/50 dark:bg-slate-900/50 border-t border-slate-200 dark:border-slate-800">
      {suggestions.map((suggestion, idx) => (
        <button
          key={idx}
          onClick={() => onSelectSuggestion(suggestion)}
          className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-white dark:bg-slate-800 border border-indigo-200 dark:border-indigo-900/60 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 hover:border-indigo-400 transition shadow-sm"
        >
          <Sparkles className="w-3 h-3 mr-1.5 text-indigo-500 shrink-0" />
          <span>{suggestion}</span>
        </button>
      ))}
    </div>
  );
};
