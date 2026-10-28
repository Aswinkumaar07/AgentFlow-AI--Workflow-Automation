import React, { useState } from 'react';
import { Search, X, Code2, Layers, Clock, Repeat, Zap, Check } from 'lucide-react';
import { useWorkflowStore } from '../../store/useWorkflowStore';

export interface VariableItem {
  name: string;
  expression: string;
  category: 'Node' | 'Loop' | 'System' | 'Trigger';
  description: string;
  sample_value?: string;
}

export interface VariablePickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectVariable?: (expression: string) => void;
  onSelect?: (expression: string) => void;
}

const DEFAULT_VARIABLES: VariableItem[] = [
  // Node Outputs
  {
    name: 'Gmail Subject',
    expression: '{{$node.Gmail.subject}}',
    category: 'Node',
    description: 'Email subject line from Gmail step',
    sample_value: 'Quarterly Invoice Update',
  },
  {
    name: 'Gmail Sender Email',
    expression: '{{$node.Gmail.sender}}',
    category: 'Node',
    description: 'Sender email address',
    sample_value: 'billing@company.com',
  },
  {
    name: 'Google Sheets Values',
    expression: '{{$node.Sheets.values}}',
    category: 'Node',
    description: 'Matrix of spreadsheet row values',
    sample_value: "[['Name', 'Email']]",
  },
  {
    name: 'Slack Message TS',
    expression: '{{$node.Slack.ts}}',
    category: 'Node',
    description: 'Slack posted message timestamp token',
    sample_value: '1698273615.000100',
  },
  {
    name: 'AI Text Summary',
    expression: '{{$node.AI.summary}}',
    category: 'Node',
    description: 'AI model generated text summary',
    sample_value: 'Summary of document content...',
  },

  // Loop Variables
  {
    name: 'Loop Current Item',
    expression: '{{$loop.item}}',
    category: 'Loop',
    description: 'Current raw item object in iteration',
    sample_value: '{"name": "Alice", "email": "alice@example.com"}',
  },
  {
    name: 'Loop Item Email',
    expression: '{{$loop.item.email}}',
    category: 'Loop',
    description: 'Extracted email field from current loop item',
    sample_value: 'alice@example.com',
  },
  {
    name: 'Loop Item Name',
    expression: '{{$loop.item.name}}',
    category: 'Loop',
    description: 'Extracted name field from current loop item',
    sample_value: 'Alice Smith',
  },
  {
    name: 'Loop Index',
    expression: '{{$loop.index}}',
    category: 'Loop',
    description: 'Zero-based loop index counter',
    sample_value: '0',
  },

  // System Variables
  {
    name: 'Current Date',
    expression: '{{$today}}',
    category: 'System',
    description: 'ISO formatted date (YYYY-MM-DD)',
    sample_value: '2026-08-04',
  },
  {
    name: 'Current Timestamp',
    expression: '{{$now}}',
    category: 'System',
    description: 'Full UTC ISO timestamp',
    sample_value: '2026-08-04T14:24:00Z',
  },
  {
    name: 'UUID Generator',
    expression: '{{$uuid}}',
    category: 'System',
    description: 'Generates a unique v4 UUID string',
    sample_value: 'a75e26ad-42a5-4f57-9355-23093b2d5175',
  },
  {
    name: 'Execution ID',
    expression: '{{$execution.id}}',
    category: 'System',
    description: 'Active workflow execution ID',
    sample_value: 'exec_99812736',
  },

  // Trigger Variables
  {
    name: 'Webhook Payload Body',
    expression: '{{trigger_payload.body}}',
    category: 'Trigger',
    description: 'Raw text or JSON payload from Webhook trigger',
    sample_value: '{"event": "user.created"}',
  },
  {
    name: 'GitHub PR Title',
    expression: '{{trigger.pull_request.title}}',
    category: 'Trigger',
    description: 'Title of triggering GitHub Pull Request',
    sample_value: 'Fix authentication bug',
  },
];

export const VariablePickerModal: React.FC<VariablePickerModalProps> = ({
  isOpen,
  onClose,
  onSelectVariable,
  onSelect,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [copiedExpr, setCopiedExpr] = useState<string | null>(null);

  const { nodes, selectedNode, edges } = useWorkflowStore();

  if (!isOpen) return null;

  // Helper to find preceding/upstream nodes in the workflow DAG
  const getUpstreamNodes = () => {
    if (!selectedNode) return nodes;
    const targetId = selectedNode.id;

    // Build set of downstream nodes reachable from selectedNode
    const downstreamSet = new Set<string>();
    downstreamSet.add(targetId);
    let added = true;
    while (added) {
      added = false;
      edges.forEach((edge) => {
        if (downstreamSet.has(edge.source) && !downstreamSet.has(edge.target)) {
          downstreamSet.add(edge.target);
          added = true;
        }
      });
    }

    return nodes.filter((n) => !downstreamSet.has(n.id));
  };

  const upstreamNodes = getUpstreamNodes();
  const dynamicNodeVars: VariableItem[] = [];

  upstreamNodes.forEach((node) => {
    const nodeId = node.id;
    const nodeData = (node.data || {}) as Record<string, any>;
    const nodeLabel = String(nodeData.label || nodeData.operation || nodeData.name || nodeId);

    const propertyKeys = new Set<string>();

    if (nodeData.response_schema?.properties && typeof nodeData.response_schema.properties === 'object') {
      Object.keys(nodeData.response_schema.properties).forEach((k) => propertyKeys.add(k));
    }

    if (nodeData.parameters && typeof nodeData.parameters === 'object') {
      Object.keys(nodeData.parameters).forEach((k) => {
        if (!k.startsWith('auth_') && !['url', 'http_method', 'method', 'is_dynamic_api'].includes(k)) {
          propertyKeys.add(k);
        }
      });
    }

    ['petId', 'id', 'status', 'quantity', 'shipDate', 'complete'].forEach((k) => propertyKeys.add(k));

    dynamicNodeVars.push({
      name: `${nodeLabel} — Full Output Data`,
      expression: `{{${nodeId}.data}}`,
      category: 'Node',
      description: `Complete JSON response object from step ${nodeId}`,
      sample_value: '{"id": 1, "petId": 100, "status": "placed"}',
    });

    propertyKeys.forEach((key) => {
      dynamicNodeVars.push({
        name: `${nodeLabel} — ${key}`,
        expression: `{{${nodeId}.data.${key}}}`,
        category: 'Node',
        description: `Output field '${key}' from step ${nodeId} (${nodeLabel})`,
        sample_value: key === 'petId' ? '100' : key === 'id' ? '1' : key === 'status' ? 'placed' : '10',
      });
    });
  });

  const allVariables = [...dynamicNodeVars, ...DEFAULT_VARIABLES];
  const categories = ['All', 'Node', 'Loop', 'System', 'Trigger'];

  const filteredVariables = allVariables.filter((item) => {
    const matchesCategory = selectedCategory === 'All' || item.category === selectedCategory;
    const matchesSearch =
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.expression.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleInsert = (expr: string) => {
    if (onSelectVariable) onSelectVariable(expr);
    if (onSelect) onSelect(expr);
    setCopiedExpr(expr);
    setTimeout(() => {
      setCopiedExpr(null);
      onClose();
    }, 400);
  };

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'Node':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300">
            <Layers className="w-3 h-3 mr-1" /> Node Output
          </span>
        );
      case 'Loop':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-300">
            <Repeat className="w-3 h-3 mr-1" /> Loop
          </span>
        );
      case 'System':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300">
            <Clock className="w-3 h-3 mr-1" /> System
          </span>
        );
      case 'Trigger':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300">
            <Zap className="w-3 h-3 mr-1" /> Trigger
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
          <div className="flex items-center space-x-2">
            <Code2 className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              Intelligent Variable Browser
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search & Tabs Controls */}
        <div className="p-4 space-y-3 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search variables (e.g. {{$node.Gmail.subject}}, {{$today}})..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex space-x-1 overflow-x-auto pb-1">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                  selectedCategory === cat
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Variables List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
          {filteredVariables.length === 0 ? (
            <div className="text-center py-10 text-slate-500 dark:text-slate-400">
              No variables found matching "{searchTerm}"
            </div>
          ) : (
            filteredVariables.map((item, idx) => (
              <div
                key={`${item.expression}_${idx}`}
                onClick={() => handleInsert(item.expression)}
                className="group flex items-center justify-between p-3.5 border border-slate-200 dark:border-slate-800 hover:border-indigo-500 dark:hover:border-indigo-500 rounded-lg cursor-pointer bg-white dark:bg-slate-800/40 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 transition"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-semibold text-sm text-indigo-600 dark:text-indigo-400 group-hover:underline">
                      {item.expression}
                    </span>
                    {getCategoryBadge(item.category)}
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                    {item.name}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    {item.description}
                  </div>
                  {item.sample_value && (
                    <div className="text-[11px] font-mono text-slate-400 dark:text-slate-500">
                      Sample: <span className="text-slate-600 dark:text-slate-300">{item.sample_value}</span>
                    </div>
                  )}
                </div>

                <div className="ml-4 shrink-0">
                  <button className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-xs font-medium shadow-sm transition flex items-center space-x-1">
                    {copiedExpr === item.expression ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>Inserted</span>
                      </>
                    ) : (
                      <span>Insert</span>
                    )}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
