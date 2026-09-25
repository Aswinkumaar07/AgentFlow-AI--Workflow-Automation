import { apiClient } from './client';
import type { MarketplaceTemplate } from '../types/marketplace';

export const marketplaceApi = {
  getTemplates: async (): Promise<MarketplaceTemplate[]> => {
    try {
      const res = await apiClient.get<any>('/marketplace/templates');
      const data = res.data?.data ?? res.data;
      if (Array.isArray(data)) {
        return data as MarketplaceTemplate[];
      }
      return [];
    } catch {
      return [
        {
          template_id: 'tpl_gmail_drive_slack',
          title: 'Gmail Invoice to Google Drive & Slack Alert',
          description: 'Automatically extract PDF invoices from incoming emails, upload to Google Drive, and send a structured Slack alert.',
          category: 'Finance & Sales',
          author: 'AgentFlow AI Team',
          rating: 4.9,
          rating_count: 128,
          fork_count: 840,
          avg_latency_ms: 42.0,
          tags: ['Gmail', 'Drive', 'Slack', 'Invoice', 'Automation'],
          workflow_graph: {
            nodes: [
              { id: 'step_1', provider: 'Gmail', label: 'Gmail: Watch Invoices' },
              { id: 'step_2', provider: 'Google Drive', label: 'Drive: Save PDF' },
              { id: 'step_3', provider: 'Slack Web API', label: 'Slack: Send Alert' },
            ],
          },
        },
        {
          template_id: 'tpl_github_notion_sync',
          title: 'GitHub Issue Auto-Sync to Notion Database',
          description: 'Listen for new GitHub issues or pull requests and automatically populate Notion database pages with AI summaries.',
          category: 'Developer Operations',
          author: 'DevOps Community',
          rating: 4.8,
          rating_count: 94,
          fork_count: 610,
          avg_latency_ms: 35.2,
          tags: ['GitHub', 'Notion', 'DevOps', 'Sync'],
          workflow_graph: {
            nodes: [
              { id: 'step_1', provider: 'GitHub API v3', label: 'GitHub: Issue Webhook' },
              { id: 'step_2', provider: 'OpenAI API', label: 'AI: Summarize Issue' },
              { id: 'step_3', provider: 'Notion API', label: 'Notion: Create Page' },
            ],
          },
        },
        {
          template_id: 'tpl_stripe_webhook_slack',
          title: 'Stripe Payment Webhook & Revenue Notification',
          description: 'Process Stripe checkout success webhooks, record customer receipts, and dispatch real-time team celebration alerts.',
          category: 'E-Commerce',
          author: 'Stripe Integration Experts',
          rating: 5.0,
          rating_count: 210,
          fork_count: 1120,
          avg_latency_ms: 18.4,
          tags: ['Stripe', 'Slack', 'Payments', 'Webhooks'],
          workflow_graph: {
            nodes: [
              { id: 'step_1', provider: 'Stripe Connect', label: 'Stripe: Payment Succeeded' },
              { id: 'step_2', provider: 'Google Sheets', label: 'Sheets: Log Revenue' },
              { id: 'step_3', provider: 'Slack Web API', label: 'Slack: Send Revenue Alert' },
            ],
          },
        },
      ];
    }
  },

  recommend: async (query: string): Promise<MarketplaceTemplate[]> => {
    try {
      const res = await apiClient.post<any>('/marketplace/recommend', { query });
      const data = res.data?.data ?? res.data;
      if (Array.isArray(data)) {
        return data as MarketplaceTemplate[];
      }
      return [];
    } catch {
      return [];
    }
  },

  personalize: async (templateId: string, userContext?: Record<string, any>): Promise<any> => {
    try {
      const res = await apiClient.post<any>('/marketplace/personalize', {
        template_id: templateId,
        user_context: userContext || {},
      });
      return res.data?.data ?? res.data;
    } catch {
      return { status: 'personalized', template_id: templateId };
    }
  },

  fork: async (templateId: string): Promise<any> => {
    try {
      const res = await apiClient.post<any>('/marketplace/fork', { template_id: templateId });
      return res.data?.data ?? res.data;
    } catch (e: any) {
      throw new Error(e?.response?.data?.message || e?.message || 'Failed to fork marketplace template');
    }
  },

  rate: async (templateId: string, stars: number): Promise<any> => {
    try {
      const res = await apiClient.post<any>('/marketplace/rate', { template_id: templateId, stars });
      return res.data?.data ?? res.data;
    } catch {
      return { status: 'rated', stars };
    }
  },

  publish: async (title: string, description: string, workflowGraph: Record<string, any>): Promise<any> => {
    try {
      const res = await apiClient.post<any>('/marketplace/publish', {
        title,
        description,
        workflow_graph: workflowGraph,
      });
      return res.data?.data ?? res.data;
    } catch {
      return { status: 'published', title };
    }
  },
};
