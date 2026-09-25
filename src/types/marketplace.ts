export interface MarketplaceTemplate {
  template_id: string;
  title: string;
  description: string;
  category: string;
  author: string;
  rating: number;
  rating_count: number;
  fork_count: number;
  avg_latency_ms: number;
  tags: string[];
  workflow_graph: Record<string, any>;
  comments?: Array<{ user: string; text: string; date: string }>;
}
