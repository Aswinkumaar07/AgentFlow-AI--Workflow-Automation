import React, { useState } from 'react';
import { Send, RefreshCw, X } from 'lucide-react';

interface CopilotInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  onCancel?: () => void;
  onRegenerate?: () => void;
}

export const CopilotInput: React.FC<CopilotInputProps> = ({
  onSendMessage,
  isLoading,
  onCancel,
  onRegenerate,
}) => {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || isLoading) return;
    onSendMessage(text.trim());
    setText('');
  };

  return (
    <form onSubmit={handleSubmit} className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
      <div className="flex items-center space-x-2">
        <input
          type="text"
          placeholder="Type your message or answer follow-up questions..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={isLoading}
          className="flex-1 px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
        />

        {onRegenerate && (
          <button
            type="button"
            onClick={onRegenerate}
            disabled={isLoading}
            title="Regenerate workflow"
            className="p-2.5 text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        )}

        {isLoading && onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            className="p-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl transition shadow-sm"
          >
            <X className="w-4 h-4" />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!text.trim() || isLoading}
            className="p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 dark:disabled:bg-slate-800 text-white rounded-xl transition shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </div>
    </form>
  );
};
