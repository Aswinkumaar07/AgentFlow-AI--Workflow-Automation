export interface OAuthProvider {
  id: string;
  name: string;
  auth_type: string;
  icon: string;
  scopes: string[];
}

export interface OAuthConnection {
  id: string;
  user_id: string;
  provider: string;
  access_token?: string;
  refresh_token?: string;
  expires_at?: number;
  scopes: string[];
  status: 'CONNECTED' | 'EXPIRED' | 'DISCONNECTED';
  created_at: number;
  updated_at?: number;
  account_label?: string;
  is_default?: boolean;
}

export interface ConnectedAccount {
  account_id: string;
  provider: string;
  email_or_name: string;
  status: 'active' | 'expired' | 'disconnected';
  is_default: boolean;
  expires_at: number;
  scopes: string[];
  connected_at?: number;
  is_expired: boolean;
  expires_in_seconds: number;
}

export interface OAuthHealthStatus {
  provider: string;
  is_connected: boolean;
  status: 'healthy' | 'expiring_soon' | 'expired' | 'missing';
  is_expired: boolean;
  expires_in_seconds: number;
  expires_at?: number;
  account_id?: string | null;
  email_or_name?: string | null;
  scopes?: string[];
  is_default?: boolean;
  message: string;
}

export interface PopulateWorkflowResult {
  steps: any[];
  bound_count: number;
  needs_auth_count: number;
  bound: Array<{ step_id: string; provider: string; account: string }>;
  needs_auth: Array<{ step_id: string; provider: string; oauth_connect_url: string }>;
  fully_authenticated: boolean;
}
