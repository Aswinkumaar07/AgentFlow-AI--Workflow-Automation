import React from 'react';
import { MessageSquare, Plus, Trash2 } from 'lucide-react';

export interface SessionItem {
  id: string;
  title: string;
  timestamp: string;
}

interface ConversationSidebarProps {
  sessions: SessionItem[];
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string) => void;
}

export const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
}) => {
  return (
    <div className="w-64 border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 flex flex-col h-full">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={onNewSession}
          className="w-full py-2 px-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition flex items-center justify-center space-x-1.5"
        >
          <Plus className="w-4 h-4" />
          <span>New AI Copilot Session</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-2 py-1">
          Recent Conversations
        </div>

        {sessions.map((sess) => (
          <div
            key={sess.id}
            onClick={() => onSelectSession(sess.id)}
            className={`group flex items-center justify-between p-2.5 rounded-lg text-xs cursor-pointer transition ${
              activeSessionId === sess.id
                ? 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-medium'
                : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60'
            }`}
          >
            <div className="flex items-center space-x-2 truncate">
              <MessageSquare className="w-3.5 h-3.5 shrink-0 text-slate-400 group-hover:text-indigo-500" />
              <span className="truncate">{sess.title}</span>
            </div>

            <button
              onClick={(e) => {
                e.stopPropagation();
                onDeleteSession(sess.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-500 rounded transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
