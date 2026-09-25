import React, { useState } from 'react';
import { Bell, CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

interface NotificationItem {
  id: string;
  type: 'error' | 'success' | 'info';
  title: string;
  message: string;
  timestamp: string;
}

export const NotificationCenter: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([
    {
      id: 'notif_1',
      type: 'error',
      title: 'Workflow Execution Failed',
      message: 'Node [step_3] failed due to Slack API rate limit.',
      timestamp: '2 mins ago',
    },
    {
      id: 'notif_2',
      type: 'info',
      title: 'Human Approval Required',
      message: 'Execution [exec_v3_9921] requires manager approval.',
      timestamp: '15 mins ago',
    },
    {
      id: 'notif_3',
      type: 'success',
      title: 'OAuth Token Refreshed',
      message: 'Google OAuth access token renewed automatically.',
      timestamp: '1 hour ago',
    },
  ]);

  const dismiss = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition"
        title="Notification Center"
      >
        <Bell className="h-5 w-5" />
        {notifications.length > 0 && (
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-destructive ring-2 ring-background" />
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-card border border-border rounded-2xl shadow-2xl overflow-hidden z-50 text-xs">
          <div className="p-3 border-b border-border flex items-center justify-between bg-muted/30">
            <h4 className="font-bold">Notifications</h4>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-primary/10 text-primary">
              {notifications.length} New
            </span>
          </div>

          <div className="max-h-72 overflow-y-auto divide-y divide-border">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-muted-foreground">No notifications.</div>
            ) : (
              notifications.map((n) => (
                <div key={n.id} className="p-3 flex items-start justify-between hover:bg-muted/20 transition gap-2">
                  <div className="flex gap-2">
                    {n.type === 'error' ? (
                      <AlertTriangle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
                    ) : n.type === 'success' ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                    ) : (
                      <Info className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <h5 className="font-bold text-foreground text-[11px]">{n.title}</h5>
                      <p className="text-[10px] text-muted-foreground mt-0.5 leading-relaxed">{n.message}</p>
                      <span className="text-[9px] text-muted-foreground/70 block mt-1">{n.timestamp}</span>
                    </div>
                  </div>
                  <button onClick={() => dismiss(n.id)} className="text-muted-foreground hover:text-foreground">
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
