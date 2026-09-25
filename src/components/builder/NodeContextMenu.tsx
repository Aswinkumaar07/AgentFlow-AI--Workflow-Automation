import React, { useEffect, useRef } from 'react';
import { Copy, Trash2, Layers, Pencil, Settings } from 'lucide-react';

interface NodeContextMenuProps {
  x: number;
  y: number;
  nodeId: string;
  nodeLabel: string;
  onDuplicate: () => void;
  onDelete: () => void;
  onCopy: () => void;
  onRename: () => void;
  onInspect: () => void;
  onClose: () => void;
}

export const NodeContextMenu: React.FC<NodeContextMenuProps> = ({
  x,
  y,
  nodeId,
  nodeLabel,
  onDuplicate,
  onDelete,
  onCopy,
  onRename,
  onInspect,
  onClose,
}) => {
  const menuRef = useRef<HTMLDivElement>(null);

  // Close on outside click or Escape
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [onClose]);

  // Clamp to viewport
  const menuWidth = 192;
  const menuHeight = 200;
  const clampedX = Math.min(x, window.innerWidth - menuWidth - 8);
  const clampedY = Math.min(y, window.innerHeight - menuHeight - 8);

  const items = [
    { icon: Settings, label: 'Inspect', action: onInspect, color: 'text-primary' },
    { icon: Pencil, label: 'Rename', action: onRename, color: 'text-foreground' },
    { icon: Copy, label: 'Copy', action: onCopy, color: 'text-foreground' },
    { icon: Layers, label: 'Duplicate', action: onDuplicate, color: 'text-foreground' },
    { icon: Trash2, label: 'Delete', action: onDelete, color: 'text-destructive' },
  ];

  return (
    <div
      ref={menuRef}
      className="fixed z-[9999] w-48 rounded-xl border border-border bg-card shadow-2xl shadow-black/30 overflow-hidden backdrop-blur-sm"
      style={{ top: clampedY, left: clampedX }}
      onContextMenu={(e) => e.preventDefault()}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-border bg-muted/30">
        <p className="text-[10px] font-mono text-muted-foreground truncate">{nodeId}</p>
        <p className="text-xs font-semibold truncate">{nodeLabel}</p>
      </div>

      {/* Actions */}
      <div className="p-1">
        {items.map(({ icon: Icon, label, action, color }) => (
          <button
            key={label}
            onClick={() => { action(); onClose(); }}
            className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs rounded-lg hover:bg-muted transition-colors ${color}`}
          >
            <Icon className="h-3.5 w-3.5 shrink-0" />
            {label}
          </button>
        ))}
      </div>
    </div>
  );
};
