import React, { useEffect, useState } from 'react';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import { workflowApi } from '../../api/workflows';
import { Clock, X, Trash2, Plus, Sparkles, CheckCircle2, PauseCircle, Webhook, Copy, Check } from 'lucide-react';

interface SchedulesTriggersModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SchedulesTriggersModal: React.FC<SchedulesTriggersModalProps> = ({ isOpen, onClose }) => {
  const { workflowId, savedVersions, fetchVersions } = useWorkflowStore();

  const [schedules, setSchedules] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [scheduleName, setScheduleName] = useState('');
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copiedWebhook, setCopiedWebhook] = useState(false);
  const [activeTab, setActiveTab] = useState<'schedules' | 'webhooks'>('schedules');

  const currentWfId = workflowId || 'wf_studio_1';
  const webhookUrl = `http://localhost:8000/api/v1/triggers/webhook/${currentWfId}`;

  const loadSchedules = async () => {
    setLoading(true);
    try {
      const data = await workflowApi.getSchedules(currentWfId);
      setSchedules(data);
    } catch (err) {
      console.error('Failed to load schedules:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchVersions();
      loadSchedules();
    }
  }, [isOpen, currentWfId]);

  useEffect(() => {
    if (savedVersions.length > 0 && !selectedVersionId) {
      setSelectedVersionId(savedVersions[0].version_id);
    }
  }, [savedVersions]);

  if (!isOpen) return null;

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const pinnedVersion = savedVersions.find((v) => v.version_id === selectedVersionId);
      await workflowApi.createSchedule(currentWfId, {
        prompt: prompt.trim(),
        name: scheduleName.trim() || undefined,
        version_id: pinnedVersion?.version_id || selectedVersionId || undefined,
        version_number: pinnedVersion?.version_number || undefined,
      });

      setPrompt('');
      setScheduleName('');
      await loadSchedules();
    } catch (err) {
      console.error('Failed to create schedule:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggle = async (scheduleId: string, currentActive: boolean) => {
    try {
      await workflowApi.toggleSchedule(currentWfId, scheduleId, !currentActive);
      await loadSchedules();
    } catch (err) {
      console.error('Failed to toggle schedule:', err);
    }
  };

  const handleDelete = async (scheduleId: string) => {
    try {
      await workflowApi.deleteSchedule(currentWfId, scheduleId);
      await loadSchedules();
    } catch (err) {
      console.error('Failed to delete schedule:', err);
    }
  };

  const copyWebhookToClipboard = () => {
    navigator.clipboard.writeText(webhookUrl);
    setCopiedWebhook(true);
    setTimeout(() => setCopiedWebhook(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-[#13102A]/95 border border-[rgba(255,255,255,0.12)] rounded-2xl shadow-2xl backdrop-blur-2xl flex flex-col max-h-[85vh] overflow-hidden text-slate-200">
        {/* Header */}
        <div className="p-4 px-6 border-b border-[rgba(255,255,255,0.10)] flex items-center justify-between bg-[#1B1728]/50">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[#FF6D00]/20 to-[#FF0C00]/10 border border-[#FF6D00]/30 text-[#FF6D00] flex items-center justify-center font-bold">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Schedules & Triggers
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-[#FF6D00]/15 text-[#FF6D00] border border-[#FF6D00]/30">
                  AI-28
                </span>
              </h2>
              <p className="text-xs text-[#A098AE]">
                Automate workflow runs using time schedules, interval timers, or webhooks with version pinning.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#A098AE] hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="px-6 border-b border-[rgba(255,255,255,0.10)] bg-[#0E0918]/60 flex space-x-6">
          <button
            onClick={() => setActiveTab('schedules')}
            className={`py-3 text-xs font-bold border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === 'schedules'
                ? 'border-[#FF6D00] text-[#FF6D00]'
                : 'border-transparent text-[#A098AE] hover:text-white'
            }`}
          >
            <Clock className="w-4 h-4" />
            Time Schedules & Intervals
          </button>
          <button
            onClick={() => setActiveTab('webhooks')}
            className={`py-3 text-xs font-bold border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === 'webhooks'
                ? 'border-[#FF6D00] text-[#FF6D00]'
                : 'border-transparent text-[#A098AE] hover:text-white'
            }`}
          >
            <Webhook className="w-4 h-4" />
            Webhook Trigger Endpoints
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-[#231E3A]">
          {activeTab === 'schedules' && (
            <>
              {/* Create Schedule Card */}
              <form onSubmit={handleCreateSchedule} className="bg-[#1B1728]/80 border border-[rgba(255,255,255,0.10)] rounded-xl p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white flex items-center gap-1.5">
                    <Plus className="w-4 h-4 text-[#FF6D00]" />
                    New Schedule
                  </span>
                  <span className="text-[11px] text-[#A098AE]">Natural language expressions supported</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#A098AE] mb-1">Schedule Prompt</label>
                    <input
                      type="text"
                      placeholder='e.g. "every 30 minutes", "every day at 9 AM"'
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      className="w-full px-3.5 py-2 text-xs bg-[#0E0918] border border-[rgba(255,255,255,0.12)] rounded-xl text-white placeholder-[#7A748E] focus:outline-none focus:border-[#FF6D00]"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-[#A098AE] mb-1">Pin Workflow Version</label>
                    <select
                      value={selectedVersionId}
                      onChange={(e) => setSelectedVersionId(e.target.value)}
                      className="w-full px-3.5 py-2 text-xs bg-[#0E0918] border border-[rgba(255,255,255,0.12)] rounded-xl text-white focus:outline-none focus:border-[#FF6D00]"
                    >
                      {savedVersions.map((v) => (
                        <option key={v.version_id} value={v.version_id}>
                          v{v.version_number} — {v.name || `Snapshot ${v.version_id}`} ({v.node_count ?? 0} nodes)
                        </option>
                      ))}
                      {savedVersions.length === 0 && <option value="">Latest Working Version</option>}
                    </select>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    placeholder="Schedule Label / Name (optional)"
                    value={scheduleName}
                    onChange={(e) => setScheduleName(e.target.value)}
                    className="flex-1 px-3.5 py-2 text-xs bg-[#0E0918] border border-[rgba(255,255,255,0.12)] rounded-xl text-white placeholder-[#7A748E] focus:outline-none focus:border-[#FF6D00]"
                  />
                  <button
                    type="submit"
                    disabled={!prompt.trim() || isSubmitting}
                    className="px-4 py-2 bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold rounded-xl hover:opacity-95 transition flex items-center gap-1.5 shadow-[0_0_15px_rgba(255,109,0,0.30)] disabled:opacity-50 disabled:shadow-none cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Create Schedule
                  </button>
                </div>
              </form>

              {/* Active Schedules List */}
              <div className="space-y-3">
                <h3 className="text-[11px] font-bold text-[#A098AE] uppercase tracking-wider">
                  Configured Schedules ({schedules.length})
                </h3>

                {loading && <div className="text-center py-6 text-xs text-[#A098AE]">Loading schedules...</div>}

                {!loading && schedules.length === 0 && (
                  <div className="text-center py-8 bg-[#0E0918]/50 border border-[rgba(255,255,255,0.08)] rounded-xl text-xs text-[#A098AE]">
                    No schedules created for this workflow yet. Create one above!
                  </div>
                )}

                {!loading &&
                  schedules.map((sch) => {
                    const isActive = sch.enabled && sch.status === 'active';
                    return (
                      <div
                        key={sch.job_id || sch.schedule_id}
                        className="bg-[#0E0918]/80 border border-[rgba(255,255,255,0.10)] rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-[#FF6D00]/30 transition-colors"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white text-xs">{sch.name}</span>
                            <span
                              className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded-full ${
                                isActive ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                              }`}
                            >
                              {isActive ? 'ACTIVE' : 'PAUSED'}
                            </span>
                            {sch.version_number && (
                              <span className="px-2 py-0.5 text-[10px] font-mono rounded-md bg-[#231E3A] text-slate-200 border border-[rgba(255,255,255,0.10)]">
                                Pinned v{sch.version_number}
                              </span>
                            )}
                          </div>

                          <div className="text-[11px] text-[#A098AE] flex flex-wrap items-center gap-x-4 gap-y-1">
                            <span>Type: <strong className="text-white">{sch.schedule_type}</strong></span>
                            {sch.prompt && <span>Prompt: <em className="text-slate-300">"{sch.prompt}"</em></span>}
                            <span>Run Count: <strong className="text-white">{sch.run_count || 0}</strong></span>
                            {sch.next_run_at && (
                              <span>Next Run: <strong className="text-[#FF6D00]">{new Date(sch.next_run_at).toLocaleTimeString()}</strong></span>
                            )}
                            {sch.last_run_at && (
                              <span>Last Run: <strong className="text-slate-300">{new Date(sch.last_run_at).toLocaleTimeString()}</strong></span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 self-end md:self-auto">
                          <button
                            onClick={() => handleToggle(sch.job_id || sch.schedule_id, isActive)}
                            title={isActive ? 'Pause Schedule' : 'Activate Schedule'}
                            className="px-2.5 py-1.5 text-xs font-semibold text-slate-200 bg-[#1B1728] border border-[rgba(255,255,255,0.10)] rounded-lg hover:bg-[#231E3A] transition-colors flex items-center gap-1.5 cursor-pointer"
                          >
                            {isActive ? (
                              <>
                                <PauseCircle className="w-3.5 h-3.5 text-amber-400" />
                                Pause
                              </>
                            ) : (
                              <>
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                                Resume
                              </>
                            )}
                          </button>

                          <button
                            onClick={() => handleDelete(sch.job_id || sch.schedule_id)}
                            title="Delete Schedule"
                            className="p-1.5 text-[#A098AE] hover:text-rose-400 bg-[#1B1728] border border-[rgba(255,255,255,0.10)] rounded-lg hover:bg-[#231E3A] transition-colors cursor-pointer"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </>
          )}

          {activeTab === 'webhooks' && (
            <div className="space-y-6">
              <div className="bg-[#0E0918]/80 border border-[rgba(255,255,255,0.10)] rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-white font-bold text-xs">
                    <Webhook className="w-4 h-4 text-[#FF6D00]" />
                    Workflow Webhook Trigger URL
                  </div>
                  <button
                    onClick={copyWebhookToClipboard}
                    className="px-2.5 py-1.5 bg-[#1B1728] border border-[rgba(255,255,255,0.10)] hover:bg-[#231E3A] text-slate-200 text-xs font-medium rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    {copiedWebhook ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedWebhook ? 'Copied URL' : 'Copy Endpoint'}
                  </button>
                </div>

                <div className="bg-[#1B1728] border border-[rgba(255,255,255,0.10)] p-3 rounded-lg font-mono text-xs text-[#FF6D00] break-all select-all">
                  POST {webhookUrl}
                </div>

                <p className="text-xs text-[#A098AE] leading-relaxed">
                  Send HTTP POST requests with any JSON body payload to automatically trigger this workflow.
                  Incoming data fields are resolved directly into expression tokens such as <code className="text-[#FF6D00] bg-[#1B1728] px-1 py-0.5 rounded text-[11px] font-mono border border-[rgba(255,255,255,0.08)]">{'{{trigger.body.customer}}'}</code> or <code className="text-[#FF6D00] bg-[#1B1728] px-1 py-0.5 rounded text-[11px] font-mono border border-[rgba(255,255,255,0.08)]">{'{{trigger.payload.amount}}'}</code>.
                </p>

                <div className="bg-[#1B1728] border border-[rgba(255,255,255,0.10)] p-4 rounded-lg space-y-2">
                  <span className="text-[11px] font-bold text-[#A098AE] uppercase tracking-wider block">cURL Example</span>
                  <pre className="text-[11px] font-mono text-slate-300 overflow-x-auto p-2.5 bg-[#0E0918] rounded-lg border border-[rgba(255,255,255,0.08)]">
{`curl -X POST "${webhookUrl}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "event": "invoice.created",
    "customer": "Acme Corp",
    "amount": 1250.00
  }'`}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
