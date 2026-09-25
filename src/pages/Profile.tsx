import { motion } from 'framer-motion';
import { GitBranch, CheckCircle, TrendingUp, Calendar, Edit } from 'lucide-react';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { Card, CardContent } from '../components/ui/card';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { mockWorkflows } from '../data/mockData';

const stats = [
  { label: 'Workflows', value: '24', icon: GitBranch },
  { label: 'Executions', value: '1,842', icon: TrendingUp },
  { label: 'Success Rate', value: '99.1%', icon: CheckCircle },
  { label: 'Member Since', value: 'Jan 2026', icon: Calendar },
];

export default function Profile() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Profile hero */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="overflow-hidden border border-border bg-card shadow-sm rounded-2xl">
            {/* Banner */}
            <div className="h-28 bg-gradient-to-r from-primary/40 via-purple-600/40 to-blue-500/40 relative">
              <div className="absolute inset-0 bg-gradient-to-r from-primary/50 via-purple-600/50 to-transparent" />
            </div>
            <CardContent className="pt-0 px-6 pb-6">
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 -mt-8">
                <div className="flex items-end gap-4">
                  <Avatar className="w-20 h-20 ring-4 ring-card shadow-xl">
                    <AvatarFallback className="text-2xl font-bold bg-primary text-primary-foreground">AK</AvatarFallback>
                  </Avatar>
                  <div className="pb-1">
                    <h2 className="text-xl font-bold text-foreground">Aswin Kumaar</h2>
                    <p className="text-xs text-muted-foreground">aswin@agentflow.ai</p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <Badge variant="default" className="text-[10px] font-bold uppercase">Enterprise Admin</Badge>
                      <Badge variant="secondary" className="text-[10px]">Owner</Badge>
                    </div>
                  </div>
                </div>
                <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                  <Edit className="w-3.5 h-3.5" /> Edit profile
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <motion.div key={s.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <Card className="p-4 border border-border bg-card shadow-sm rounded-2xl">
                  <div className="flex items-center gap-2 text-muted-foreground mb-2">
                    <Icon className="w-4 h-4 text-primary" />
                    <span className="text-xs font-semibold">{s.label}</span>
                  </div>
                  <p className="text-2xl font-extrabold text-foreground tracking-tight font-mono">{s.value}</p>
                </Card>
              </motion.div>
            );
          })}
        </div>

        {/* Recent Workflows */}
        <Card className="p-5 border border-border bg-card shadow-sm rounded-2xl space-y-3">
          <h3 className="font-bold text-sm">Recent Active Workflows</h3>
          <div className="space-y-2">
            {mockWorkflows.slice(0, 3).map((wf) => (
              <div key={wf.id} className="p-3 rounded-xl border border-border bg-background flex items-center justify-between">
                <div>
                  <p className="font-semibold text-xs text-foreground">{wf.name}</p>
                  <p className="text-[10px] text-muted-foreground font-mono">{(wf as any).provider || (wf as any).description || 'Workflow Integration'} · {(wf as any).stepCount || 3} steps</p>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase">
                  ACTIVE
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
