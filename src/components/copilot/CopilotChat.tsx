import React, { useState } from 'react';
import { Bot, Sparkles } from 'lucide-react';
import { CopilotMessage, type MessageProps } from './CopilotMessage';
import { CopilotSuggestions } from './CopilotSuggestions';
import { CopilotInput } from './CopilotInput';
import { ConversationSidebar, type SessionItem } from './ConversationSidebar';
import { apiClient } from '../../api/client';
import { useWorkflowStore } from '../../store/useWorkflowStore';

export const CopilotChat: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>('session_default');
  const [sessions, setSessions] = useState<SessionItem[]>([
    { id: 'session_default', title: 'Send Email Workflow', timestamp: new Date().toISOString() },
  ]);
  const [messages, setMessages] = useState<MessageProps[]>([
    {
      role: 'assistant',
      message: 'Hello! I am your AgentFlow AI Copilot. What workflow goal would you like to build today?',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [suggestions, setSuggestions] = useState<string[]>([
    'Send a good morning email',
    'Notify Slack when GitHub PR opens',
    'Read employees from Google Sheets and email each employee',
    'Webhook -> AI summarize text -> Email customer',
  ]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [latestGraph, setLatestGraph] = useState<any>(null);

  const handleSendMessage = async (userMsg: string) => {
    const userTurn: MessageProps = {
      role: 'user',
      message: userMsg,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userTurn]);
    setIsLoading(true);

    try {
      const resp = await apiClient.post('/copilot/chat', {
        session_id: sessionId,
        message: userMsg,
      });

      const data = resp.data;
      const aiMessage = data.message;
      const isReady = data.is_ready_to_generate;
      const newSuggestions = data.suggested_replies || [];
      const proposedGraph = data.proposed_graph;

      if (proposedGraph) {
        setLatestGraph(proposedGraph);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          message: aiMessage,
          timestamp: new Date().toISOString(),
          isReadyToGenerate: isReady,
          proposedGraph: proposedGraph,
        },
      ]);
      setSuggestions(newSuggestions);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          message: 'Sorry, I encountered an error processing your request. Please try again.',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateWorkflow = () => {
    if (latestGraph) {
      const rawNodes = latestGraph.nodes || [];
      const rawEdges = latestGraph.edges || [];

      const formattedNodes = rawNodes.map((n: any, idx: number) => ({
        id: n.id || `node_${idx}`,
        type: 'custom',
        position: { x: 250, y: 100 + idx * 120 },
        data: { label: n.label || n.id, provider: n.provider, operation: n.operation_id, parameters: n.parameters },
      }));

      const formattedEdges = rawEdges.map((e: any) => ({
        id: e.id || `edge_${e.source}_${e.target}`,
        source: e.source,
        target: e.target,
      }));

      useWorkflowStore.getState().setNodes(formattedNodes);
      useWorkflowStore.getState().setEdges(formattedEdges);
      alert('Workflow DAG synthesized and rendered on canvas!');
    }
  };

  const handleNewSession = () => {
    const newId = `session_${Date.now()}`;
    const newSess: SessionItem = {
      id: newId,
      title: 'New Workflow Session',
      timestamp: new Date().toISOString(),
    };
    setSessions((prev) => [newSess, ...prev]);
    setSessionId(newId);
    setMessages([
      {
        role: 'assistant',
        message: 'Started a new session! What workflow would you like to build?',
        timestamp: new Date().toISOString(),
      },
    ]);
    setSuggestions([
      'Send a good morning email',
      'Notify Slack when GitHub PR opens',
    ]);
    setLatestGraph(null);
  };

  return (
    <div className="flex h-full bg-white dark:bg-slate-900 overflow-hidden">
      <ConversationSidebar
        sessions={sessions}
        activeSessionId={sessionId}
        onSelectSession={setSessionId}
        onNewSession={handleNewSession}
        onDeleteSession={(id) => setSessions((prev) => prev.filter((s) => s.id !== id))}
      />

      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">AI Copilot Assistant</h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Conversational Workflow Co-Authoring</p>
            </div>
          </div>
        </div>

        {/* Chat Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((m, idx) => (
            <CopilotMessage
              key={idx}
              role={m.role}
              message={m.message}
              timestamp={m.timestamp}
              isReadyToGenerate={m.isReadyToGenerate}
              proposedGraph={m.proposedGraph}
              onGenerateClick={handleGenerateWorkflow}
            />
          ))}

          {isLoading && (
            <div className="flex items-center space-x-2 text-slate-400 text-xs py-2">
              <Sparkles className="w-4 h-4 animate-spin text-indigo-500" />
              <span>AI Copilot is reasoning...</span>
            </div>
          )}
        </div>

        {/* Suggestions & Input */}
        <CopilotSuggestions suggestions={suggestions} onSelectSuggestion={handleSendMessage} />
        <CopilotInput onSendMessage={handleSendMessage} isLoading={isLoading} onRegenerate={handleGenerateWorkflow} />
      </div>
    </div>
  );
};
