import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useExecutionStore } from '../../store/useExecutionStore';
import { Terminal, Download, Search, Copy, Trash2, CheckCircle2 } from 'lucide-react';

const LEVEL_CFG = {
  INFO:  { text: 'text-blue-400',    bg: 'bg-blue-500/10',    border: 'border-blue-500/30', label: 'INFO'  },
  WARN:  { text: 'text-amber-400',   bg: 'bg-amber-500/10',   border: 'border-amber-500/30', label: 'WARN'  },
  ERROR: { text: 'text-rose-400',    bg: 'bg-rose-500/10',    border: 'border-rose-500/30', label: 'ERROR' },
};

const MIN_HEIGHT = 48;
const MAX_HEIGHT = 480;
const DEFAULT_HEIGHT = 210;

function copyText(text: string) {
  navigator.clipboard?.writeText(text).catch(() => {});
}

export const LiveLogsPanel: React.FC = () => {
  const { logs, downloadLogs } = useExecutionStore();
  const clearLogs = () => useExecutionStore.setState({ logs: [] });

  const [filterLevel, setFilterLevel] = useState<string>('ALL');
  const [search, setSearch] = useState('');
  const [panelHeight, setPanelHeight] = useState(DEFAULT_HEIGHT);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const logEndRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ startY: number; startH: number } | null>(null);

  // Auto-scroll to bottom on new logs
  useEffect(() => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs.length, autoScroll]);

  // Detect manual scroll
  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const atBottom = scrollHeight - scrollTop - clientHeight < 20;
    setAutoScroll(atBottom);
  };

  // Resize drag handlers
  const handleDragStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    dragRef.current = { startY: e.clientY, startH: panelHeight };
    const onMove = (ev: MouseEvent) => {
      if (!dragRef.current) return;
      const delta = dragRef.current.startY - ev.clientY;
      const newH = Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, dragRef.current.startH + delta));
      setPanelHeight(newH);
    };
    const onUp = () => {
      dragRef.current = null;
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [panelHeight]);

  const handleCopyLine = (log: { id: string; timestamp: string; level: string; step_id?: string; message: string }) => {
    const text = `[${log.timestamp}] [${log.level}]${log.step_id ? ` [${log.step_id}]` : ''} ${log.message}`;
    copyText(text);
    setCopiedId(log.id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const filteredLogs = logs.filter((log) => {
    const matchesLevel = filterLevel === 'ALL' || log.level === filterLevel;
    const matchesSearch =
      !search ||
      log.message.toLowerCase().includes(search.toLowerCase()) ||
      (log.step_id?.toLowerCase().includes(search.toLowerCase()) ?? false);
    return matchesLevel && matchesSearch;
  });

  const errorCount = logs.filter((l) => l.level === 'ERROR').length;
  const warnCount  = logs.filter((l) => l.level === 'WARN').length;

  return (
    <div
      className="border-t border-[rgba(255,255,255,0.12)] bg-[#0E0918]/95 backdrop-blur-md flex flex-col font-mono text-xs overflow-hidden"
      style={{ height: panelHeight }}
    >
      {/* Drag Handle */}
      <div
        onMouseDown={handleDragStart}
        className="h-2 w-full cursor-ns-resize bg-[#1B1728] hover:bg-[#FF6D00]/30 transition flex items-center justify-center shrink-0"
        title="Drag to resize panel"
      >
        <div className="w-10 h-1 rounded-full bg-[rgba(255,255,255,0.2)]" />
      </div>

      {/* Panel Header Toolbar */}
      <div className="px-4 py-2 border-b border-[rgba(255,255,255,0.08)] bg-[#13102A] flex items-center justify-between gap-3 shrink-0 flex-wrap">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-[#FF6D00]" />
          <span className="font-bold text-white text-xs">Live Console Logs</span>
          <span className="text-[10px] text-[rgba(255,255,255,0.4)] font-mono">({logs.length})</span>
        </div>

        {/* Level Filters */}
        <div className="flex items-center gap-1.5">
          {['ALL', 'INFO', 'WARN', 'ERROR'].map((lvl) => {
            const isAct = filterLevel === lvl;
            const count = lvl === 'ERROR' ? errorCount : lvl === 'WARN' ? warnCount : logs.length;
            return (
              <button
                key={lvl}
                onClick={() => setFilterLevel(lvl)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition flex items-center gap-1 ${
                  isAct
                    ? 'bg-[#FF6D00] text-black shadow-sm'
                    : 'bg-[#1B1728] text-[rgba(255,255,255,0.6)] hover:text-white border border-[rgba(255,255,255,0.08)]'
                }`}
              >
                <span>{lvl}</span>
                {lvl !== 'ALL' && <span className="opacity-80">({count})</span>}
              </button>
            );
          })}
        </div>

        {/* Search & Actions */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-[rgba(255,255,255,0.4)]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search logs..."
              className="pl-7 pr-3 py-1 bg-[#1B1728] border border-[rgba(255,255,255,0.1)] rounded-lg text-[11px] text-white placeholder-[rgba(255,255,255,0.3)] focus:outline-none focus:border-[#FF6D00]"
            />
          </div>

          <button
            onClick={clearLogs}
            className="p-1.5 rounded-lg border border-[rgba(255,255,255,0.1)] bg-[#1B1728] hover:bg-[#231E3A] text-[rgba(255,255,255,0.6)] hover:text-white transition"
            title="Clear Console Logs"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>

          <button
            onClick={downloadLogs}
            className="p-1.5 rounded-lg border border-[rgba(255,255,255,0.1)] bg-[#1B1728] hover:bg-[#231E3A] text-[rgba(255,255,255,0.6)] hover:text-white transition"
            title="Download Logs"
          >
            <Download className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Log Output Stream */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 p-4 overflow-y-auto space-y-1 scrollbar-none font-mono text-[11px] leading-relaxed"
      >
        {filteredLogs.length === 0 ? (
          <p className="text-[rgba(255,255,255,0.4)] text-center py-6">
            {logs.length === 0 ? 'Console ready — execute a workflow to stream live logs.' : 'No logs match current filter.'}
          </p>
        ) : (
          filteredLogs.map((log) => {
            const cfg = LEVEL_CFG[log.level as keyof typeof LEVEL_CFG] ?? LEVEL_CFG.INFO;
            return (
              <div
                key={log.id}
                className="group flex items-start justify-between gap-3 py-0.5 hover:bg-[#1B1728]/80 px-2 rounded-lg transition"
              >
                <div className="flex items-start gap-2.5 min-w-0 flex-1">
                  <span className="text-[rgba(255,255,255,0.35)] shrink-0">{log.timestamp}</span>
                  <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold shrink-0 ${cfg.bg} ${cfg.text}`}>
                    {cfg.label}
                  </span>
                  {log.step_id && (
                    <span className="text-[#FF6D00] shrink-0 font-semibold">[{log.step_id}]</span>
                  )}
                  <span className="text-[rgba(255,255,255,0.85)] break-all">{log.message}</span>
                </div>

                <button
                  onClick={() => handleCopyLine(log)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-[rgba(255,255,255,0.4)] hover:text-white transition shrink-0"
                  title="Copy log line"
                >
                  {copiedId === log.id ? <CheckCircle2 className="h-3 w-3 text-[#22C55E]" /> : <Copy className="h-3 w-3" />}
                </button>
              </div>
            );
          })
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
};
