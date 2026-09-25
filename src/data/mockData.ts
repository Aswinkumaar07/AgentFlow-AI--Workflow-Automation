import type { Workflow, HistoryEntry, User, Notification } from '../types';

// ─── Mock User ───────────────────────────────────────────────────────────────
export const mockUser: User = {
  id: 'usr-001',
  name: 'Aswin Kumar',
  email: 'aswin@agentflow.ai',
  role: 'admin',
  plan: 'pro',
  createdAt: '2026-01-15T10:00:00Z',
};

// ─── Mock Workflows ──────────────────────────────────────────────────────────
export const mockWorkflows: Workflow[] = [
  {
    id: 'wf-001',
    name: 'GitHub PR → Jira + Slack',
    description: 'Creates Jira ticket and posts Slack message on every new PR',
    status: 'success',
    createdAt: '2026-07-01T10:00:00Z',
    updatedAt: '2026-07-18T08:30:00Z',
    lastRun: '2 hours ago',
    executionCount: 312,
    successCount: 301,
    tags: ['github', 'jira', 'slack'],
    prompt: 'When a GitHub PR is opened in repo agentflow-core, create a Jira ticket in AF project and notify #dev-team on Slack',
  },
  {
    id: 'wf-002',
    name: 'Stripe → QuickBooks + Email',
    description: 'Mirrors Stripe payments as QB invoices and sends receipt',
    status: 'running',
    createdAt: '2026-07-05T09:00:00Z',
    updatedAt: '2026-07-18T09:00:00Z',
    lastRun: '5 mins ago',
    executionCount: 204,
    successCount: 198,
    tags: ['stripe', 'quickbooks', 'email'],
    prompt: 'For every successful Stripe payment, create an invoice in QuickBooks and email the customer a receipt',
  },
  {
    id: 'wf-003',
    name: 'Support Form → Zendesk + CRM',
    description: 'Creates Zendesk ticket and HubSpot lead from form submissions',
    status: 'pending',
    createdAt: '2026-07-10T14:00:00Z',
    updatedAt: '2026-07-17T16:00:00Z',
    lastRun: 'Yesterday',
    executionCount: 87,
    successCount: 82,
    tags: ['zendesk', 'hubspot', 'forms'],
    prompt: 'When a contact form is submitted, open a Zendesk ticket and create a HubSpot lead with submitted data',
  },
  {
    id: 'wf-004',
    name: 'Twitter Monitor → Alert',
    description: 'Monitors brand mentions and sends sentiment-scored Slack alerts',
    status: 'success',
    createdAt: '2026-07-08T08:00:00Z',
    updatedAt: '2026-07-18T07:45:00Z',
    lastRun: '30 mins ago',
    executionCount: 567,
    successCount: 543,
    tags: ['twitter', 'slack', 'monitoring'],
  },
  {
    id: 'wf-005',
    name: 'Daily RSS → Newsletter',
    description: 'Compiles top RSS posts into daily Mailchimp newsletter draft',
    status: 'success',
    createdAt: '2026-07-01T07:00:00Z',
    updatedAt: '2026-07-18T06:00:00Z',
    lastRun: '3 hours ago',
    executionCount: 631,
    successCount: 627,
    tags: ['rss', 'mailchimp', 'content'],
  },
  {
    id: 'wf-006',
    name: 'Airtable → Google Sheets Sync',
    description: 'Bi-directional sync between Airtable base and Google Sheets',
    status: 'error',
    createdAt: '2026-07-12T11:00:00Z',
    updatedAt: '2026-07-17T20:00:00Z',
    lastRun: '12 hours ago',
    executionCount: 156,
    successCount: 140,
    tags: ['airtable', 'google-sheets', 'sync'],
  },
];

// ─── Mock History ────────────────────────────────────────────────────────────
export const mockHistory: HistoryEntry[] = [
  { id: 'h1', workflowId: 'wf-001', workflowName: 'GitHub PR → Jira + Slack', status: 'success', triggeredAt: '2026-07-18T08:30:00Z', duration: 1240, trigger: 'Webhook' },
  { id: 'h2', workflowId: 'wf-002', workflowName: 'Stripe → QuickBooks + Email', status: 'running', triggeredAt: '2026-07-18T10:05:00Z', duration: 0, trigger: 'Stripe Event' },
  { id: 'h3', workflowId: 'wf-004', workflowName: 'Twitter Monitor → Alert', status: 'success', triggeredAt: '2026-07-18T09:42:00Z', duration: 820, trigger: 'Cron 15m' },
  { id: 'h4', workflowId: 'wf-006', workflowName: 'Airtable → Google Sheets Sync', status: 'error', triggeredAt: '2026-07-17T20:00:00Z', duration: 5100, trigger: 'Manual' },
  { id: 'h5', workflowId: 'wf-005', workflowName: 'Daily RSS → Newsletter', status: 'success', triggeredAt: '2026-07-18T06:00:00Z', duration: 3200, trigger: 'Daily Cron' },
  { id: 'h6', workflowId: 'wf-003', workflowName: 'Support Form → Zendesk + CRM', status: 'success', triggeredAt: '2026-07-17T16:45:00Z', duration: 980, trigger: 'Form Submit' },
  { id: 'h7', workflowId: 'wf-001', workflowName: 'GitHub PR → Jira + Slack', status: 'success', triggeredAt: '2026-07-17T14:22:00Z', duration: 1150, trigger: 'Webhook' },
  { id: 'h8', workflowId: 'wf-002', workflowName: 'Stripe → QuickBooks + Email', status: 'success', triggeredAt: '2026-07-17T12:10:00Z', duration: 2340, trigger: 'Stripe Event' },
];

// ─── Mock Notifications ──────────────────────────────────────────────────────
export const mockNotifications: Notification[] = [
  { id: 'n1', title: 'Workflow Failed', message: 'Airtable → Sheets sync failed at step 3', type: 'error', read: false, createdAt: '2026-07-17T20:00:00Z' },
  { id: 'n2', title: 'New Execution', message: 'GitHub PR workflow ran successfully', type: 'success', read: false, createdAt: '2026-07-18T08:30:00Z' },
  { id: 'n3', title: 'API Rate Limit', message: 'Twitter API approaching rate limit', type: 'warning', read: true, createdAt: '2026-07-18T07:00:00Z' },
  { id: 'n4', title: 'Workflow Activated', message: 'Daily RSS Newsletter is now active', type: 'info', read: true, createdAt: '2026-07-17T06:00:00Z' },
];

// ─── Analytics mock data ─────────────────────────────────────────────────────
export const analyticsExecutions = [
  { day: 'Jul 12', count: 42, success: 38 },
  { day: 'Jul 13', count: 67, success: 61 },
  { day: 'Jul 14', count: 55, success: 52 },
  { day: 'Jul 15', count: 89, success: 84 },
  { day: 'Jul 16', count: 73, success: 68 },
  { day: 'Jul 17', count: 95, success: 88 },
  { day: 'Jul 18', count: 112, success: 107 },
];

export const analyticsResponseTime = [
  { hour: '00:00', ms: 820 }, { hour: '03:00', ms: 640 }, { hour: '06:00', ms: 1100 },
  { hour: '09:00', ms: 1840 }, { hour: '12:00', ms: 2100 }, { hour: '15:00', ms: 1650 },
  { hour: '18:00', ms: 1300 }, { hour: '21:00', ms: 940 },
];

export const analyticsApiUsage = [
  { name: 'GitHub', value: 312 },
  { name: 'Slack', value: 287 },
  { name: 'Stripe', value: 204 },
  { name: 'Jira', value: 156 },
  { name: 'Others', value: 189 },
];

// ─── Example prompts for Workflow Builder ─────────────────────────────────────
export const examplePrompts = [
  'When a GitHub PR is opened, create a Jira ticket and notify the team on Slack with PR details',
  'For every successful Stripe payment, create a QuickBooks invoice and email the customer a receipt',
  'Every morning at 9am, fetch top Hacker News posts and email a curated digest to subscribers',
  'When a support form is submitted, create a Zendesk ticket and add the lead to HubSpot CRM',
  'Monitor Twitter for brand mentions, analyze sentiment, and post alerts to Slack if negative',
  'Sync Airtable records to Google Sheets every hour and send a summary report by email',
];

// ─── Nav items ───────────────────────────────────────────────────────────────
export const sidebarItems = [
  { id: 'dashboard', label: 'Dashboard', path: '/dashboard', icon: 'LayoutDashboard' },
  { id: 'builder', label: 'Workflow Builder', path: '/builder', icon: 'Wand2', badge: 'New' },
  { id: 'history', label: 'History', path: '/history', icon: 'History' },
  { id: 'analytics', label: 'Analytics', path: '/analytics', icon: 'BarChart3' },
  { id: 'settings', label: 'Settings', path: '/settings', icon: 'Settings' },
];
