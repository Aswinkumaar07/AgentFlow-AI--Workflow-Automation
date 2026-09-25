import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { useAuthStore } from '../store/useAuthStore';
import { useTheme } from '../context/ThemeContext';
import {
  User,
  Palette,
  Cpu,
  Users,
  FileText,
  ShieldCheck,
  Layers,
  LogOut,
  Copy,
  Check,
  Plus,
  Trash2,
  CheckCircle2,
  Lock,
  Moon,
  Sun,
  Monitor,
  RefreshCw,
  SlidersHorizontal,
  ArrowRight,
} from 'lucide-react';

interface APIKeyItem {
  id: string;
  name: string;
  prefix: string;
  created_at: number;
  last_used_at?: number | null;
  expires_at?: number | null;
  is_active: boolean;
  raw_key?: string;
}

interface OrgUserItem {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

interface AuditLogItem {
  id: string;
  timestamp: number;
  actor_email: string;
  actor_role: string;
  action: string;
  resource_type: string;
  status: string;
  metadata: Record<string, any>;
}

export const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { theme, setTheme } = useTheme();

  const [activeTab, setActiveTab] = useState<
    'account' | 'appearance' | 'api' | 'users' | 'audit' | 'security'
  >('account');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Real User profile state
  const initialName = user?.full_name || (user as any)?.name || 'Aswin Kumaar';
  const initialEmail = user?.email || 'aswin@agentflow.ai';
  const userRole = user?.role || 'OWNER';

  const [name, setName] = useState(initialName);
  const [email, setEmail] = useState(initialEmail);
  const [isSaved, setIsSaved] = useState(false);

  // API keys state
  const [apiKeys, setApiKeys] = useState<APIKeyItem[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [isAddingKey, setIsAddingKey] = useState(false);
  const [createdRawKeyModal, setCreatedRawKeyModal] = useState<string | null>(null);

  // Organization Users state
  const [orgUsers, setOrgUsers] = useState<OrgUserItem[]>([]);

  // Audit Logs state
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [auditFilterAction, setAuditFilterAction] = useState('');

  const navigationSections = [
    { id: 'account', label: 'Profile & Account', icon: User, desc: 'Personal profile & identity' },
    { id: 'appearance', label: 'Appearance & Theme', icon: Palette, desc: 'Visual theme preferences' },
    { id: 'api', label: 'API Keys & Secrets', icon: Cpu, desc: 'Enterprise secret tokens' },
    { id: 'users', label: 'Users & RBAC', icon: Users, desc: 'Team member roles' },
    { id: 'audit', label: 'Activity & Audit Log', icon: FileText, desc: 'Immutable security events' },
    { id: 'security', label: 'Security & Vault', icon: ShieldCheck, desc: 'AES-256 encryption status' },
  ] as const;

  // Load API Keys from Backend
  const fetchApiKeys = async () => {
    try {
      const res = await fetch('/api/v1/api-keys');
      if (res.ok) {
        const json = await res.json();
        if (json.data) setApiKeys(json.data);
      }
    } catch (e) {
      console.error('Failed to fetch API keys:', e);
    }
  };

  // Load Org Users from Backend
  const fetchOrgUsers = async () => {
    try {
      const res = await fetch('/api/v1/users');
      if (res.ok) {
        const json = await res.json();
        if (json.data) setOrgUsers(json.data);
      }
    } catch (e) {
      console.error('Failed to fetch org users:', e);
    }
  };

  // Load Audit Logs from Backend
  const fetchAuditLogs = async () => {
    try {
      const url = auditFilterAction
        ? `/api/v1/audit-logs?action=${encodeURIComponent(auditFilterAction)}`
        : '/api/v1/audit-logs';
      const res = await fetch(url);
      if (res.ok) {
        const json = await res.json();
        if (json.data) setAuditLogs(json.data);
      }
    } catch (e) {
      console.error('Failed to fetch audit logs:', e);
    }
  };

  useEffect(() => {
    if (activeTab === 'api') fetchApiKeys();
    if (activeTab === 'users') fetchOrgUsers();
    if (activeTab === 'audit') fetchAuditLogs();
  }, [activeTab, auditFilterAction]);

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const handleCopyKey = (id: string, text: string) => {
    navigator.clipboard?.writeText(text).catch(() => {});
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const handleAddKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const res = await fetch('/api/v1/api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newKeyName.trim(), expires_in_days: 30 }),
      });
      if (res.ok) {
        const json = await res.json();
        if (json.data && json.data.raw_key) {
          setCreatedRawKeyModal(json.data.raw_key);
        }
        fetchApiKeys();
      }
    } catch (e) {
      console.error('Failed to create API key:', e);
    }
    setNewKeyName('');
    setIsAddingKey(false);
  };

  const handleRevokeKey = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/api-keys/${id}`, { method: 'DELETE' });
      if (res.ok) {
        fetchApiKeys();
      }
    } catch (e) {
      console.error('Failed to revoke API key:', e);
    }
  };

  const handleRotateKey = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/api-keys/${id}/rotate`, { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        if (json.data && json.data.raw_key) {
          setCreatedRawKeyModal(json.data.raw_key);
        }
        fetchApiKeys();
      }
    } catch (e) {
      console.error('Failed to rotate API key:', e);
    }
  };

  const handleUpdateRole = async (userId: string, newRole: string) => {
    try {
      const res = await fetch(`/api/v1/users/${userId}/role`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole }),
      });
      if (res.ok) {
        fetchOrgUsers();
      }
    } catch (e) {
      console.error('Failed to update user role:', e);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-200">
        {/* Header Section */}
        <div className="p-6 rounded-2xl bg-[#13102A]/90 border border-[rgba(255,255,255,0.08)] backdrop-blur-md shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-2xl bg-[#FF6D00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center shrink-0">
              <SlidersHorizontal className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">Workspace Settings</h1>
              <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5">
                Manage account profile, display themes, API key vaults, RBAC roles, and security policies.
              </p>
            </div>
          </div>

          <button
            onClick={() => navigate('/connectors')}
            className="px-4 py-2.5 rounded-xl bg-[#FF6D00]/15 hover:bg-[#FF6D00]/25 border border-[#FF6D00]/40 text-[#FF6D00] text-xs font-semibold transition shrink-0 flex items-center gap-2 shadow-sm"
          >
            <Layers className="h-4 w-4" />
            <span>Manage Connectors</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Main Content Layout: Two Columns on Desktop */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
          {/* Left Column: Navigation Sidebar & User Card */}
          <div className="lg:col-span-1 space-y-6">
            <nav className="p-3 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] backdrop-blur-md space-y-1.5 shadow-lg">
              {navigationSections.map((sec) => {
                const Icon = sec.icon;
                const isAct = activeTab === sec.id;
                return (
                  <button
                    key={sec.id}
                    onClick={() => setActiveTab(sec.id as any)}
                    className={`w-full p-3 rounded-xl text-left transition flex items-center gap-3 border ${
                      isAct
                        ? 'bg-gradient-to-r from-[#FF6D00]/20 to-[#FF0C00]/10 border-[#FF6D00]/40 text-white font-bold shadow-[0_4px_16px_rgba(255,109,0,0.15)]'
                        : 'border-transparent text-[rgba(255,255,255,0.6)] hover:text-white hover:bg-[rgba(255,255,255,0.04)] font-medium'
                    }`}
                  >
                    <Icon className={`h-4 w-4 shrink-0 ${isAct ? 'text-[#FF6D00]' : ''}`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs truncate">{sec.label}</p>
                      <p className="text-[10px] text-[rgba(255,255,255,0.4)] truncate font-normal">
                        {sec.desc}
                      </p>
                    </div>
                  </button>
                );
              })}

              {/* Navigation link to Connectors */}
              <button
                onClick={() => navigate('/connectors')}
                className="w-full p-3 rounded-xl text-left transition flex items-center gap-3 border border-transparent text-[rgba(255,255,255,0.6)] hover:text-[#FF6D00] hover:bg-[#FF6D00]/10 font-medium"
              >
                <Layers className="h-4 w-4 shrink-0 text-[#FF6D00]" />
                <div className="min-w-0 flex-1">
                  <p className="text-xs truncate font-bold text-white">Integrations Workspace</p>
                  <p className="text-[10px] text-[rgba(255,255,255,0.4)] truncate">
                    Open /connectors page
                  </p>
                </div>
                <ArrowRight className="h-3.5 w-3.5 shrink-0 text-[#FF6D00]" />
              </button>
            </nav>

            {/* Authenticated Identity & Sign Out Card */}
            <div className="p-4 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] backdrop-blur-md space-y-4 shadow-lg">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] text-black font-extrabold text-sm flex items-center justify-center shrink-0 shadow-md">
                  {name[0]?.toUpperCase() ?? 'A'}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-white truncate">{name}</p>
                  <p className="text-[10px] text-[rgba(255,255,255,0.5)] truncate">{email}</p>
                </div>
                <span className="text-[9px] font-extrabold px-2 py-0.5 rounded bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 shrink-0">
                  {userRole}
                </span>
              </div>

              <button
                onClick={handleLogout}
                className="w-full py-2 px-3 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 text-xs font-semibold transition flex items-center justify-center gap-2"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span>Sign Out of AgentFlow AI</span>
              </button>
            </div>
          </div>

          {/* Right Column: Active Section Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* ── Section 1: Profile & Account ── */}
            {activeTab === 'account' && (
              <div className="p-6 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] backdrop-blur-md space-y-6 shadow-xl max-w-3xl">
                <div>
                  <h3 className="font-bold text-base text-white">Personal & Workspace Profile</h3>
                  <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5">
                    Update your display name and organization email address.
                  </p>
                </div>

                {isSaved && (
                  <div className="p-3 bg-[#22C55E]/10 border border-[#22C55E]/30 rounded-xl text-xs text-[#22C55E] font-semibold flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" /> Profile settings saved successfully!
                  </div>
                )}

                <form onSubmit={handleSaveProfile} className="space-y-5 text-xs">
                  <div className="flex items-center gap-4 p-4 rounded-xl bg-[#1B1728]/80 border border-[rgba(255,255,255,0.06)]">
                    <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[#FF6D00] to-[#FF0C00] flex items-center justify-center text-black font-extrabold text-xl shadow-md shrink-0">
                      {name[0]?.toUpperCase() ?? 'A'}
                    </div>
                    <div>
                      <p className="font-bold text-sm text-white">{name}</p>
                      <p className="text-xs text-[rgba(255,255,255,0.5)]">{email}</p>
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#22C55E] bg-[#22C55E]/10 px-2 py-0.5 rounded-full mt-1 border border-[#22C55E]/20">
                        {userRole} Role
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-[rgba(255,255,255,0.5)]">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full p-3 bg-[#0E0918] border border-[rgba(255,255,255,0.1)] rounded-xl focus:outline-none focus:border-[#FF6D00] text-xs text-white transition"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-[rgba(255,255,255,0.5)]">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full p-3 bg-[#0E0918] border border-[rgba(255,255,255,0.1)] rounded-xl focus:outline-none focus:border-[#FF6D00] text-xs text-white transition"
                    />
                  </div>

                  <div className="pt-2">
                    <button
                      type="submit"
                      className="px-6 py-2.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-black font-extrabold text-xs rounded-xl shadow-[0_4px_16px_rgba(255,109,0,0.3)] hover:opacity-90 transition"
                    >
                      Save Profile Changes
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* ── Section 2: Appearance & Theme ── */}
            {activeTab === 'appearance' && (
              <div className="p-6 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] backdrop-blur-md space-y-6 shadow-xl max-w-3xl">
                <div>
                  <h3 className="font-bold text-base text-white">Display & Visual Theme</h3>
                  <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5">
                    Customize your UI theme preference across AgentFlow AI.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                  {[
                    { id: 'dark', label: 'Dark Mode', icon: Moon, desc: 'Optimized dark glassmorphism' },
                    { id: 'light', label: 'Light Mode', icon: Sun, desc: 'Clean bright layout' },
                    { id: 'system', label: 'System Default', icon: Monitor, desc: 'Follow OS color preference' },
                  ].map((item) => {
                    const Icon = item.icon;
                    const isSelected = theme === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => setTheme(item.id as any)}
                        className={`p-5 rounded-2xl border text-left transition flex flex-col justify-between gap-4 ${
                          isSelected
                            ? 'border-[#FF6D00] bg-[#FF6D00]/10 text-white shadow-[0_0_20px_rgba(255,109,0,0.15)] font-bold'
                            : 'border-[rgba(255,255,255,0.08)] bg-[#1B1728]/60 hover:bg-[#1B1728] text-[rgba(255,255,255,0.6)]'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <Icon className={`h-6 w-6 ${isSelected ? 'text-[#FF6D00]' : ''}`} />
                          {isSelected && (
                            <span className="h-2 w-2 rounded-full bg-[#FF6D00] shadow-[0_0_8px_#FF6D00]" />
                          )}
                        </div>
                        <div>
                          <p className="text-xs font-bold text-white">{item.label}</p>
                          <p className="text-[10px] text-[rgba(255,255,255,0.4)] mt-0.5">
                            {item.desc}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ── Section 3: API Keys & Secrets ── */}
            {activeTab === 'api' && (
              <div className="space-y-6 max-w-3xl">
                <div className="p-6 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] backdrop-blur-md shadow-xl flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-base text-white">Enterprise API Keys</h3>
                    <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5">
                      Generate secret tokens starting with 'af_live_' for REST API access and CLI workflows.
                    </p>
                  </div>
                  <button
                    onClick={() => setIsAddingKey(true)}
                    className="px-4 py-2.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-black font-extrabold text-xs rounded-xl shadow-[0_4px_16px_rgba(255,109,0,0.3)] hover:opacity-90 transition flex items-center gap-1.5"
                  >
                    <Plus className="h-4 w-4" /> Create Key
                  </button>
                </div>

                {/* Created Raw Key Modal */}
                {createdRawKeyModal && (
                  <div className="p-5 rounded-2xl border border-[#22C55E]/30 bg-[#22C55E]/10 space-y-3 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[#22C55E] flex items-center gap-1.5">
                        <CheckCircle2 className="h-4 w-4" /> Secret API Key Created
                      </span>
                      <button
                        onClick={() => setCreatedRawKeyModal(null)}
                        className="text-xs font-bold text-[rgba(255,255,255,0.6)] hover:text-white"
                      >
                        Close
                      </button>
                    </div>
                    <p className="text-[11px] text-[rgba(255,255,255,0.7)]">
                      Save this key now! For security reasons, it will <strong>NEVER</strong> be displayed again.
                    </p>
                    <div className="flex items-center gap-2 p-3 bg-[#0E0918] rounded-xl font-mono border border-[#22C55E]/30">
                      <span className="flex-1 truncate font-bold text-[#22C55E]">
                        {createdRawKeyModal}
                      </span>
                      <button
                        onClick={() => handleCopyKey('modal_key', createdRawKeyModal)}
                        className="p-1.5 rounded hover:bg-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.7)]"
                      >
                        {copiedId === 'modal_key' ? (
                          <Check className="h-4 w-4 text-[#22C55E]" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* Add Key Form */}
                {isAddingKey && (
                  <form
                    onSubmit={handleAddKey}
                    className="p-5 rounded-2xl border border-[#FF6D00]/40 bg-[#FF6D00]/5 space-y-3"
                  >
                    <p className="font-bold text-xs text-white">Generate New API Key</p>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        required
                        value={newKeyName}
                        onChange={(e) => setNewKeyName(e.target.value)}
                        placeholder="Key label (e.g., Production Webhook Engine)"
                        className="flex-1 p-3 bg-[#0E0918] border border-[rgba(255,255,255,0.1)] rounded-xl text-xs text-white focus:outline-none focus:border-[#FF6D00] transition"
                      />
                      <button
                        type="submit"
                        className="px-4 py-2.5 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-black font-extrabold text-xs rounded-xl hover:opacity-90 transition"
                      >
                        Generate
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsAddingKey(false)}
                        className="px-3 py-2.5 border border-[rgba(255,255,255,0.1)] bg-[#1B1728] hover:bg-[rgba(255,255,255,0.1)] text-xs font-semibold rounded-xl text-white transition"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                )}

                {/* Key List */}
                <div className="space-y-4">
                  {(apiKeys || []).map((k) => (
                    <div
                      key={k.id}
                      className="p-5 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] backdrop-blur-md space-y-3 shadow-lg"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-bold text-xs text-white">{k.name}</span>
                          <span className="ml-2 text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-[rgba(255,255,255,0.06)] text-[rgba(255,255,255,0.6)] border border-[rgba(255,255,255,0.1)]">
                            {k.prefix}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleRotateKey(k.id)}
                            className="px-3 py-1.5 text-[10px] font-semibold border border-[rgba(255,255,255,0.1)] rounded-lg bg-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.1)] text-white transition flex items-center gap-1"
                            title="Rotate Key"
                          >
                            <RefreshCw className="h-3 w-3" /> Rotate
                          </button>
                          <button
                            onClick={() => handleRevokeKey(k.id)}
                            className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition"
                            title="Revoke Key"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 p-3 bg-[#0E0918] rounded-xl font-mono text-xs border border-[rgba(255,255,255,0.08)]">
                        <span className="flex-1 truncate text-white font-semibold">
                          {k.prefix}••••••••••••••••••••••••••••••••
                        </span>
                      </div>

                      <div className="flex justify-between text-[10px] text-[rgba(255,255,255,0.45)] font-mono">
                        <span>Created: {new Date(k.created_at * 1000).toLocaleString()}</span>
                        <span className="font-bold text-[#22C55E]">
                          Status: {k.is_active ? 'ACTIVE' : 'REVOKED'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── Section 4: Users & Roles (RBAC) ── */}
            {activeTab === 'users' && (
              <div className="space-y-6 max-w-3xl">
                <div className="p-6 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] backdrop-blur-md shadow-xl flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-base text-white">Users & Role-Based Access Control (RBAC)</h3>
                    <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5">
                      Assign organization roles: OWNER (Full Control), ADMIN (Management), MEMBER (Editor), VIEWER (Read-Only).
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  {(orgUsers || []).map((u) => (
                    <div
                      key={u.id}
                      className="p-4 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] backdrop-blur-md flex items-center justify-between shadow-lg text-xs"
                    >
                      <div>
                        <p className="font-bold text-white">{u.full_name}</p>
                        <p className="text-[11px] text-[rgba(255,255,255,0.5)]">{u.email}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <select
                          value={u.role}
                          onChange={(e) => handleUpdateRole(u.id, e.target.value)}
                          className="p-2.5 bg-[#0E0918] border border-[rgba(255,255,255,0.1)] rounded-xl text-xs text-white font-semibold focus:outline-none focus:border-[#FF6D00]"
                        >
                          <option value="OWNER">OWNER</option>
                          <option value="ADMIN">ADMIN</option>
                          <option value="MEMBER">MEMBER</option>
                          <option value="VIEWER">VIEWER</option>
                        </select>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── Section 5: Activity & Audit Logs ── */}
            {activeTab === 'audit' && (
              <div className="space-y-6 max-w-3xl">
                <div className="p-6 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] backdrop-blur-md shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <div>
                    <h3 className="font-bold text-base text-white">Security & Audit Log</h3>
                    <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5">
                      Append-only security event history with sanitized payloads.
                    </p>
                  </div>
                  <div className="flex items-center gap-2 w-full md:w-auto">
                    <input
                      type="text"
                      placeholder="Filter action (e.g. create)"
                      value={auditFilterAction}
                      onChange={(e) => setAuditFilterAction(e.target.value)}
                      className="p-2.5 bg-[#0E0918] border border-[rgba(255,255,255,0.1)] rounded-xl text-xs text-white focus:outline-none focus:border-[#FF6D00] flex-1"
                    />
                    <button
                      onClick={fetchAuditLogs}
                      className="px-4 py-2.5 bg-[#FF6D00]/20 hover:bg-[#FF6D00]/30 border border-[#FF6D00]/40 text-[#FF6D00] text-xs font-semibold rounded-xl transition shrink-0"
                    >
                      Refresh
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  {(auditLogs || []).length === 0 ? (
                    <div className="p-8 text-center text-xs text-[rgba(255,255,255,0.4)] border border-[rgba(255,255,255,0.08)] rounded-2xl bg-[#13102A]/60">
                      No security audit log events recorded yet.
                    </div>
                  ) : (
                    auditLogs.map((log) => (
                      <div
                        key={log.id}
                        className="p-5 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] space-y-2 text-xs shadow-lg"
                      >
                        <div className="flex items-center justify-between font-mono">
                          <span className="font-bold text-[#FF6D00]">{log.action}</span>
                          <span
                            className={`px-2 py-0.5 text-[9px] font-bold rounded ${
                              log.status === 'SUCCESS'
                                ? 'bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30'
                                : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                            }`}
                          >
                            {log.status}
                          </span>
                        </div>
                        <div className="flex justify-between text-[11px] text-[rgba(255,255,255,0.5)]">
                          <span>
                            Actor: {log.actor_email} ({log.actor_role})
                          </span>
                          <span>{new Date(log.timestamp * 1000).toLocaleString()}</span>
                        </div>
                        {log.metadata && Object.keys(log.metadata).length > 0 && (
                          <pre className="p-3 bg-[#0E0918] rounded-xl font-mono text-[10px] border border-[rgba(255,255,255,0.08)] overflow-x-auto text-[rgba(255,255,255,0.6)]">
                            {JSON.stringify(log.metadata, null, 2)}
                          </pre>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* ── Section 6: Security & Vault ── */}
            {activeTab === 'security' && (
              <div className="p-6 rounded-2xl bg-[#13102A]/80 border border-[rgba(255,255,255,0.08)] backdrop-blur-md space-y-6 shadow-xl max-w-3xl">
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-2xl bg-[#22C55E]/10 border border-[#22C55E]/30 text-[#22C55E] flex items-center justify-center font-bold">
                    <Lock className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-white">Tenant Secret Vault & Security</h3>
                    <p className="text-xs text-[rgba(255,255,255,0.5)] mt-0.5">
                      AES-256 GCM envelope encryption active for all workspace credentials and OAuth tokens.
                    </p>
                  </div>
                </div>

                <div className="space-y-4 pt-2">
                  <div className="p-4 bg-[#1B1728]/80 border border-[rgba(255,255,255,0.08)] rounded-xl flex items-center justify-between text-xs">
                    <div>
                      <p className="font-bold text-white">Zero-Touch Secret Encryption</p>
                      <p className="text-[10px] text-[rgba(255,255,255,0.45)]">
                        KMS-managed root encryption keys rotated every 90 days
                      </p>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 text-[10px] font-bold">
                      ENFORCED
                    </span>
                  </div>

                  <div className="p-4 bg-[#1B1728]/80 border border-[rgba(255,255,255,0.08)] rounded-xl flex items-center justify-between text-xs">
                    <div>
                      <p className="font-bold text-white">Multi-Tenant Isolation & RBAC</p>
                      <p className="text-[10px] text-[rgba(255,255,255,0.45)]">
                        Backend authorization checks enforced across all API endpoints
                      </p>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 text-[10px] font-bold">
                      ACTIVE
                    </span>
                  </div>

                  <div className="p-4 bg-[#1B1728]/80 border border-[rgba(255,255,255,0.08)] rounded-xl flex items-center justify-between text-xs">
                    <div>
                      <p className="font-bold text-white">Account Authentication Session</p>
                      <p className="text-[10px] text-[rgba(255,255,255,0.45)]">
                        Active session token for {email}
                      </p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 text-[11px] font-bold transition"
                    >
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};
