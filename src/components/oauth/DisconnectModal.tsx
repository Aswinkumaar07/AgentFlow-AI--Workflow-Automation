import React, { useEffect, useState } from 'react';
import { AlertTriangle, X, Loader2 } from 'lucide-react';

interface DisconnectModalProps {
  isOpen: boolean;
  providerName: string;
  onConfirm: () => Promise<void>;
  onClose: () => void;
}

export const DisconnectModal: React.FC<DisconnectModalProps> = ({
  isOpen,
  providerName,
  onConfirm,
  onClose,
}) => {
  const [isDisconnecting, setIsDisconnecting] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleDisconnect = async () => {
    setIsDisconnecting(true);
    try {
      await onConfirm();
    } finally {
      setIsDisconnecting(false);
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/65 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="disconnect-modal-title"
    >
      <div className="w-full max-w-[460px] bg-[#13102A] border border-[rgba(255,255,255,0.12)] rounded-2xl shadow-[0_16px_48px_rgba(0,0,0,0.6)] p-6 space-y-5 relative">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-rose-500/10 border border-rose-500/25 text-rose-500 flex items-center justify-center shrink-0">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <h3 id="disconnect-modal-title" className="font-bold text-lg text-white tracking-tight">
              Disconnect {providerName}?
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-[rgba(255,255,255,0.08)] text-[rgba(255,255,255,0.45)] hover:text-white transition"
            aria-label="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="space-y-2 text-left">
          <p className="text-sm text-white/90 font-medium leading-relaxed">
            Disconnecting <span className="font-semibold text-white">{providerName}</span> will revoke its OAuth connection.
          </p>
          <p className="text-xs text-[rgba(255,255,255,0.5)] leading-relaxed">
            Any active workflows depending on {providerName} may fail until the connection is restored.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 px-4 rounded-xl border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.1)] text-white text-xs md:text-sm font-semibold transition active:scale-95"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDisconnect}
            disabled={isDisconnecting}
            className="flex-1 py-2.5 px-4 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs md:text-sm font-semibold transition active:scale-95 flex items-center justify-center gap-2 shadow-lg shadow-rose-900/30 disabled:opacity-50"
          >
            {isDisconnecting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Disconnecting…</span>
              </>
            ) : (
              `Disconnect ${providerName}`
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
