import React from 'react';
import { Bot, User, CheckCircle, Sparkles } from 'lucide-react';

export interface MessageProps {
  role: 'user' | 'assistant';
  message: string;
  timestamp?: string;
  isReadyToGenerate?: boolean;
  proposedGraph?: any;
  onGenerateClick?: () => void;
}

export const CopilotMessage: React.FC<MessageProps> = ({
  role,
  message,
  timestamp,
  isReadyToGenerate,
  onGenerateClick,
}) => {
  const isUser = role === 'user';

  return (
    <div className={`flex space-x-3 ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow-sm">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div className={`max-w-[80%] space-y-2`}>
        <div
          className={`p-4 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-indigo-600 text-white rounded-br-none shadow-sm'
              : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 text-slate-900 dark:text-slate-100 rounded-bl-none shadow-sm'
          }`}
        >
          <div className="whitespace-pre-wrap">{message}</div>

          {isReadyToGenerate && onGenerateClick && (
            <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center space-x-1">
                <CheckCircle className="w-4 h-4" />
                <span>Ready to Synthesize DAG</span>
              </span>
              <button
                onClick={onGenerateClick}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium text-xs shadow-md transition flex items-center space-x-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate Workflow</span>
              </button>
            </div>
          )}
        </div>

        {timestamp && (
          <div className={`text-[10px] text-slate-400 dark:text-slate-500 ${isUser ? 'text-right' : 'text-left'}`}>
            {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-slate-700 dark:bg-slate-600 flex items-center justify-center text-white shrink-0 shadow-sm">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
};
