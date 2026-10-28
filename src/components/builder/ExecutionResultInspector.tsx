import React from 'react';
import { CheckCircle2, AlertCircle, Mail, Hash, FileText, Check, Copy, User, Calendar, Tag, AlertTriangle, Paperclip, Image, Download, Eye, Sparkles, GitBranch, Repeat, ShieldCheck } from 'lucide-react';
import { extractGmailMessageDetails, extractMultipleGmailMessageDetails, formatFileSize, type ExtractedAttachment } from '../../utils/gmailNormalizer';
import { extractSlackResultDetails } from '../../utils/slackNormalizer';
import { useExecutionStore } from '../../store/useExecutionStore';

export interface ExecutionResultInspectorProps {
  executionResult: {
    ok?: boolean;
    success?: boolean;
    status?: string;
    execution_id?: string;
    nodes_executed?: number;
    total_nodes?: number;
    node_results?: any[];
    final_output?: any;
    errors?: any[];
    can_resume?: boolean;
    checkpoint_timestamp?: number;
    version_id?: string;
    version_number?: number;
    trigger_type?: string;
  };
  onClose?: () => void;
  onResume?: (executionId: string) => void;
  onExecuteSuccess?: (result: any) => void;
}

// ── Attachment Gallery & Lightbox Component ─────────────────────────────────
export const AttachmentGalleryView: React.FC<{ attachments: ExtractedAttachment[]; messageId: string }> = ({
  attachments,
  messageId,
}) => {
  const [activeLightboxIndex, setActiveLightboxIndex] = React.useState<number | null>(null);

  React.useEffect(() => {
    if (!attachments || attachments.length === 0) {
      console.log(`[AI-21][NO_ATTACHMENTS] message_id=${messageId}`);
    } else {
      console.log(`[AI-21][ATTACHMENT_UI] count=${attachments.length} message_id=${messageId}`);
    }
  }, [attachments, messageId]);

  if (!attachments || attachments.length === 0) {
    return (
      <div className="p-2 rounded bg-muted/20 border border-border/40 font-mono text-[10px] text-muted-foreground flex items-center justify-between">
        <span className="flex items-center gap-1">
          <Paperclip className="h-3 w-3" /> No attachments
        </span>
      </div>
    );
  }

  const imageAttachments = attachments.filter((att) => att.isImage);
  const fileAttachments = attachments.filter((att) => !att.isImage);

  const getAttachmentUrl = (att: ExtractedAttachment) => {
    if (att.data && (att.data.startsWith('data:') || att.data.startsWith('http'))) {
      return att.data;
    }
    if (att.attachmentId) {
      const filenameEnc = encodeURIComponent(att.filename);
      const mimeEnc = encodeURIComponent(att.mimeType);
      return `/api/v1/gmail/messages/${messageId}/attachments/${att.attachmentId}?filename=${filenameEnc}&mime_type=${mimeEnc}`;
    }
    return '';
  };

  const handleDownload = (att: ExtractedAttachment) => {
    const url = getAttachmentUrl(att);
    const token = localStorage.getItem('token') || 'mock_jwt_token';
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        if (!res.ok) throw new Error('Download failed');
        return res.blob();
      })
      .then((blob) => {
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = att.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);
      })
      .catch((err) => {
        console.error('Attachment download failed:', err);
        alert(`Unable to download attachment: ${err.message}`);
      });
  };

  return (
    <div className="space-y-2 pt-1 border-t border-border/40">
      <div className="flex items-center justify-between text-[10px]">
        <span className="font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1 font-sans">
          <Paperclip className="h-3.5 w-3.5 text-primary" /> ATTACHMENTS — {attachments.length}
        </span>
      </div>

      {/* Image Gallery */}
      {imageAttachments.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {imageAttachments.map((att, idx) => {
            const isAvailable = att.available !== false;
            return (
              <div
                key={idx}
                className="group relative rounded-lg border border-border bg-background overflow-hidden flex flex-col shadow-xs hover:shadow-md transition"
              >
                <div className="h-20 bg-muted/40 relative flex items-center justify-center overflow-hidden font-mono text-[9px] text-muted-foreground">
                  {isAvailable ? (
                    <img
                      src={getAttachmentUrl(att)}
                      alt={att.filename}
                      className="w-full h-full object-cover cursor-pointer hover:scale-105 transition duration-200"
                      onClick={() => setActiveLightboxIndex(idx)}
                    />
                  ) : (
                    <div className="p-2 text-center text-muted-foreground/70 flex flex-col items-center gap-1 font-sans">
                      <Image className="h-4 w-4 opacity-50" />
                      <span>{att.filename}</span>
                    </div>
                  )}
                  {isAvailable && (
                    <button
                      onClick={() => setActiveLightboxIndex(idx)}
                      className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white transition font-sans text-[10px] font-semibold gap-1"
                    >
                      <Eye className="h-3.5 w-3.5" /> Preview
                    </button>
                  )}
                </div>
                <div className="p-1.5 flex items-center justify-between gap-1 text-[10px]">
                  <span className="font-medium truncate font-mono text-foreground" title={att.filename}>
                    {att.filename}
                  </span>
                  <div className="flex items-center gap-1 shrink-0">
                    <span className="text-[9px] font-mono text-muted-foreground">{formatFileSize(att.size)}</span>
                    {isAvailable && (
                      <button
                        onClick={() => handleDownload(att)}
                        className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                        title="Download"
                      >
                        <Download className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Non-Image Files */}
      {fileAttachments.length > 0 && (
        <div className="space-y-1">
          {fileAttachments.map((att, idx) => {
            const isAvailable = att.available !== false;
            return (
              <div
                key={idx}
                className="p-2 rounded-lg border border-border bg-background flex items-center justify-between text-[11px] font-mono shadow-2xs hover:border-primary/40 transition"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Paperclip className="h-3.5 w-3.5 text-primary shrink-0" />
                  <span className="truncate font-semibold text-foreground">{att.filename}</span>
                  <span className="text-[9px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded shrink-0">
                    {formatFileSize(att.size)}
                  </span>
                </div>
                {isAvailable && (
                  <button
                    onClick={() => handleDownload(att)}
                    className="p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition flex items-center gap-1 text-[10px] font-sans font-medium"
                  >
                    <Download className="h-3 w-3" /> Download
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Lightbox Modal */}
      {activeLightboxIndex !== null && imageAttachments[activeLightboxIndex] && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-xs"
          onClick={() => setActiveLightboxIndex(null)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] bg-card rounded-2xl overflow-hidden border border-border p-2 space-y-2 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-border text-xs font-mono">
              <span className="font-bold text-foreground truncate">{imageAttachments[activeLightboxIndex].filename}</span>
              <button
                onClick={() => setActiveLightboxIndex(null)}
                className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground font-bold text-sm"
              >
                ✕
              </button>
            </div>
            <div className="max-h-[75vh] flex items-center justify-center overflow-auto bg-black/20 rounded-xl p-2">
              <img
                src={getAttachmentUrl(imageAttachments[activeLightboxIndex])}
                alt={imageAttachments[activeLightboxIndex].filename}
                className="max-h-[70vh] object-contain rounded-lg shadow-md"
              />
            </div>
            <div className="flex items-center justify-between px-3 py-1 text-[10px] text-muted-foreground font-mono">
              <span>
                {activeLightboxIndex + 1} of {imageAttachments.length} images
              </span>
              <button
                onClick={() => handleDownload(imageAttachments[activeLightboxIndex])}
                className="px-3 py-1 rounded bg-primary text-primary-foreground font-sans font-semibold flex items-center gap-1 hover:bg-primary/90 transition"
              >
                <Download className="h-3 w-3" /> Download
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ── Reusable Safe Rendering Helper ──────────────────────────────────────────
const renderSafeValue = (value: unknown): React.ReactNode => {
  if (value === null || value === undefined) return '—';

  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return String(value);
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-muted-foreground font-mono">[ ]</span>;
    return (
      <div className="space-y-1 my-1">
        {value.map((item, index) => (
          <div key={index} className="p-1.5 rounded bg-background/60 border border-border/40 font-mono text-xs">
            {renderSafeValue(item)}
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === 'object') {
    return (
      <pre className="p-2.5 rounded-lg bg-slate-950 text-emerald-400 border border-slate-800 font-mono text-[11px] overflow-x-auto max-h-48 whitespace-pre-wrap my-1">
        {JSON.stringify(value, null, 2)}
      </pre>
    );
  }

  return String(value);
};

export function resolveApprovalTargetDetails(executionResult: any, selectedStepId?: string | null): {
  targetExecId: string | null;
  targetNodeId: string | undefined;
} {
  const nodeResults = executionResult?.node_results || [];

  const targetExecId =
    executionResult?.execution_id && executionResult.execution_id !== 'exec_live'
      ? executionResult.execution_id
      : (nodeResults.find((r: any) => r.execution_id && r.execution_id !== 'exec_live')?.execution_id || null);

  let targetNodeId: string | undefined = undefined;

  if (selectedStepId) {
    const selectedNode = nodeResults.find((r: any) => r.node_id === selectedStepId || r.step_id === selectedStepId);
    const provider = String(selectedNode?.provider || selectedNode?.operation || '').toLowerCase();
    const isWaiting = ['WAITING', 'PENDING', 'PAUSED', 'WAITING_FOR_APPROVAL'].includes(selectedNode?.status);
    if (provider.includes('approval') || isWaiting) {
      targetNodeId = selectedStepId;
    }
  }

  if (!targetNodeId) {
    const approvalNode = nodeResults.find((r: any) => {
      const provider = String(r.provider || r.operation || '').toLowerCase();
      const isWaiting = ['WAITING', 'PENDING', 'PAUSED', 'WAITING_FOR_APPROVAL'].includes(r.status);
      return provider.includes('approval') || isWaiting;
    });
    if (approvalNode) {
      targetNodeId = approvalNode.node_id || approvalNode.step_id;
    }
  }

  return { targetExecId, targetNodeId };
}

// ── Component Internal Details ──────────────────────────────────────────────
const ExecutionResultInspectorInner: React.FC<ExecutionResultInspectorProps> = ({
  executionResult,
  onClose,
  onResume,
  onExecuteSuccess,
}) => {
  const [copiedId, setCopiedId] = React.useState<string | null>(null);
  const [selectedStepId, setSelectedStepId] = React.useState<string | null>(null);
  const [isResuming, setIsResuming] = React.useState(false);

  if (!executionResult) return null;

  const isSuccess = executionResult.ok || executionResult.success || executionResult.status === 'COMPLETED';
  const nodeResults = executionResult.node_results || [];
  const nodesExecuted = executionResult.nodes_executed ?? nodeResults.filter((r) => r.status === 'SUCCESS' || r.status === 'COMPLETED').length;
  const skippedCount = nodeResults.filter((r) => r.status === 'SKIPPED').length;
  const totalNodes = executionResult.total_nodes ?? (nodeResults.length > 0 ? nodeResults.length : 1);
  const execId = executionResult.execution_id || 'exec_live';
  const canResume = Boolean(executionResult.can_resume) || ['PAUSED', 'WAITING', 'FAILED', 'CANCELLED'].includes(executionResult.status || '');
  const checkpointTs = executionResult.checkpoint_timestamp;

  const [isApproving, setIsApproving] = React.useState(false);

  const handleResumeClick = async () => {
    if (onResume) {
      onResume(execId);
      return;
    }
    setIsResuming(true);
    try {
      const res = await fetch(`/api/v1/runtime/${execId}/resume`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.execution_id) {
          useExecutionStore.getState().applyRealExecutionResult(
            data.execution_id,
            data.status || 'COMPLETED',
            data.node_results || [],
            data.final_output
          );
        }
        if (onExecuteSuccess) {
          onExecuteSuccess(data);
        }
      }
    } catch (err) {
      console.error('Failed to resume execution:', err);
    } finally {
      setIsResuming(false);
    }
  };

  const handleApproveClick = async () => {
    const { targetExecId, targetNodeId } = resolveApprovalTargetDetails(executionResult, selectedStepId);
    const finalExecId = targetExecId || (executionResult?.execution_id !== 'exec_live' ? executionResult?.execution_id : null);

    if (!finalExecId) {
      console.error('Failed to approve human step: no valid execution_id available');
      return;
    }

    setIsApproving(true);
    try {
      const url = targetNodeId
        ? `/api/v1/runtime/${encodeURIComponent(finalExecId)}/approve?node_id=${encodeURIComponent(targetNodeId)}`
        : `/api/v1/runtime/${encodeURIComponent(finalExecId)}/approve`;

      const res = await fetch(url, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.execution_id) {
          useExecutionStore.getState().applyRealExecutionResult(
            data.execution_id,
            data.status || 'COMPLETED',
            data.node_results || [],
            data.final_output
          );
        }
        if (onExecuteSuccess) {
          onExecuteSuccess(data);
        }
      } else {
        const errText = await res.text().catch(() => '');
        console.error(`Approval request failed (${res.status}): ${errText}`);
      }
    } catch (err) {
      console.error('Failed to approve human step:', err);
    } finally {
      setIsApproving(false);
    }
  };

  // Default selected step: first failed step or first step
  React.useEffect(() => {
    if (nodeResults && nodeResults.length > 0) {
      const failed = nodeResults.find((r: any) => r.status !== 'SUCCESS' && r.status !== 'COMPLETED' && r.status !== 'SKIPPED');
      const target = failed
        ? (failed.node_id || failed.id)
        : (nodeResults[0].node_id || nodeResults[0].id || 'step_1');
      setSelectedStepId(target);
    } else {
      setSelectedStepId(null);
    }
  }, [executionResult]);

  const isValidStep = Boolean(selectedStepId && nodeResults.some((r: any) => (r.node_id || r.id) === selectedStepId));
  const activeStepId = isValidStep
    ? selectedStepId
    : (nodeResults.length > 0 ? (nodeResults[0].node_id || nodeResults[0].id) : null);

  const currentStep = nodeResults.find(
    (r: any) => (r.node_id || r.id) === activeStepId
  ) || null;

  const currentOperation = currentStep ? (currentStep.operation || currentStep.operation_id || null) : null;
  const currentProvider = currentStep ? String(currentStep.provider || (currentOperation ? currentOperation.split('.')[0] : '') || '').toLowerCase() : null;
  const currentStatus = currentStep ? currentStep.status : null;
  const currentOutput = currentStep ? (currentStep.output || currentStep) : null;
  const currentStepSuccess = currentStatus === 'SUCCESS' || currentStatus === 'COMPLETED';

  // AI-29 Retry Telemetry
  const currentAttempts = currentStep?.attempts || currentStep?.attempts_history?.length || 1;
  const currentMaxAttempts = currentStep?.max_attempts || 1;
  const isRecoveredAfterRetry = currentStep?.recovered_after_retry || (currentStepSuccess && currentAttempts > 1);
  const isExhaustedRetries = currentStep?.exhausted_retries || (!currentStepSuccess && currentAttempts >= currentMaxAttempts && currentStep?.retryable);
  const isRetryableError = currentStep?.retryable || false;

  // Extract Gmail details for current step or execution result
  const singleEmail = extractGmailMessageDetails(currentStep || executionResult);
  const multiResult = extractMultipleGmailMessageDetails(currentStep || executionResult);
  const emailList = multiResult.emails;

  // Operation classification
  const isSlackOp = Boolean(currentStep && (currentProvider === 'slack' || (currentOperation && currentOperation.includes('slack'))));
  const isAIOp = Boolean(currentStep && (currentProvider === 'ai' || (currentOperation && currentOperation.includes('ai.'))));
  const isGmailOp = Boolean(currentStep && (currentProvider === 'gmail' || (currentOperation && currentOperation.includes('gmail'))));
  const isGmailSendOp = Boolean(isGmailOp && (
    (currentOperation && currentOperation.includes('send')) ||
    (currentStep?.operation && String(currentStep.operation).includes('send')) ||
    Boolean(singleEmail.recipient)
  ));
  const isConditionOp = Boolean(currentStep && (currentProvider === 'condition' || currentProvider === 'if' || (currentOperation && (currentOperation.includes('condition') || currentOperation.includes('if')))));
  const isLoopOp = Boolean(currentStep && (currentProvider === 'loop' || currentProvider === 'iterator' || (currentOperation && (currentOperation.includes('loop') || currentOperation.includes('forEach') || currentOperation.includes('iterator')))));
  const isApprovalOp = Boolean(currentStep && (currentProvider === 'approval' || currentProvider === 'human_approval' || (currentOperation && currentOperation.includes('approval'))));
  const isListOrSearch = Boolean(currentOperation && (currentOperation.includes('list') || currentOperation.includes('search')));

  // Condition node ID resolution for skipped steps
  const conditionNode = nodeResults.find((r: any) => 
    (r.operation || r.operation_id || '').includes('condition') || 
    r.provider === 'condition'
  );
  const conditionNodeId = conditionNode ? (conditionNode.node_id || conditionNode.id) : null;
  const rawReason = currentOutput?.reason || currentOutput?.output?.reason || currentStep?.reason;

  let skippedReasonText = 'Branch unselected by condition node';
  if (rawReason && rawReason !== 'Skipped due to condition evaluation') {
    skippedReasonText = rawReason;
  } else if (conditionNodeId) {
    skippedReasonText = `Branch unselected by condition node ${conditionNodeId}`;
  }

  const handleCopyId = (idText: string) => {
    navigator.clipboard.writeText(idText);
    setCopiedId(idText);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const responseObj = currentOutput?.response || currentOutput?.body || currentOutput?.result || currentOutput;

  // ── Slack Output Details Normalization ──
  const { slackResult, slackChannel, slackTs, slackText, slackOk, slackError } = extractSlackResultDetails(
    currentOutput,
    currentStepSuccess,
    currentStep
  );

  if (isSlackOp && currentStatus !== 'SKIPPED') {
    console.log('[SLACK_INSPECTOR_DIAGNOSTIC]', {
      execId,
      activeStepId,
      currentOperation,
      currentOutputKeys: Object.keys(currentOutput || {}),
      resultKeys: currentOutput?.result ? Object.keys(currentOutput.result) : null,
      outputKeys: currentOutput?.output ? Object.keys(currentOutput.output) : null,
      responseKeys: currentOutput?.response ? Object.keys(currentOutput.response) : null,
      slackResultKeys: Object.keys(slackResult || {}),
      slackChannel,
      slackTs,
      slackTextSnippet: slackText ? slackText.substring(0, 35) : null,
      slackOk,
    });
  }

  // AI Output Details
  const getBackendResponseBody = (obj: any) => {
    if (!obj) return null;
    if (typeof obj === 'string') return obj;
    if (typeof obj.body === 'string') return obj.body;
    if (typeof obj.data === 'string') return obj.data;
    return null;
  };

  const getStringVal = (val: any): string | null => {
    return typeof val === 'string' && val.trim() ? val.trim() : null;
  };

  const responseBody = responseObj && typeof responseObj.body === 'object' && responseObj.body !== null ? responseObj.body : null;
  const currentOutputBody = currentOutput && typeof currentOutput.body === 'object' && currentOutput.body !== null ? currentOutput.body : null;

  const aiSummaryText =
    getStringVal(currentOutput?.summary) ||
    getStringVal(currentOutput?.text) ||
    getStringVal(responseObj?.summary) ||
    getStringVal(responseObj?.text) ||
    getStringVal(responseBody?.summary) ||
    getStringVal(responseBody?.text) ||
    getStringVal(currentOutputBody?.summary) ||
    getStringVal(currentOutputBody?.text) ||
    getBackendResponseBody(responseObj) ||
    getBackendResponseBody(currentOutput) ||
    'No output summary available.';

  const totalMatching = multiResult.totalCount || emailList.length;
  const isPartialTruncated = totalMatching > emailList.length;
  const showingText = isPartialTruncated
    ? `Showing first ${emailList.length} of ${totalMatching} results`
    : `Showing ${emailList.length} ${emailList.length === 1 ? 'result' : 'results'}`;

  const isMultiView = isGmailOp && (emailList.length > 1 || (
    emailList.length === 1 && (
      multiResult.totalCount >= 1 || 
      isListOrSearch || 
      Boolean(responseObj?.messages) || 
      Boolean(responseObj?.items)
    )
  ));

  const statusStr = executionResult.status || (isSuccess ? 'COMPLETED' : 'FAILED');
  const isWaiting = ['WAITING', 'WAITING_FOR_APPROVAL', 'PAUSED'].includes(statusStr);

  return (
    <div className="p-4 rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#13102A]/90 backdrop-blur-2xl shadow-2xl text-xs space-y-3 font-sans">
      {/* Banner Header */}
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.10)] pb-2.5">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-xl flex items-center justify-center ${
            isSuccess
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
              : isWaiting
              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              : 'bg-red-500/10 text-red-400 border border-red-500/20'
          }`}>
            {isSuccess ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            ) : isWaiting ? (
              <Repeat className="h-4 w-4 text-amber-400" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-400" />
            )}
          </div>
          <div>
            <div className="font-bold text-white text-xs flex items-center gap-1.5">
              <span>
                {isSuccess
                  ? '✓ Workflow COMPLETED'
                  : isWaiting
                  ? `⏸ Workflow ${statusStr}`
                  : '✕ Workflow FAILED'}
              </span>
              <span className="text-[11px] font-normal text-[#A098AE] font-mono">
                — {nodesExecuted}/{totalNodes} nodes executed{skippedCount > 0 ? ` (${skippedCount} skipped)` : ''}
              </span>
            </div>
            <p className="text-[10px] text-[#A098AE] font-mono">
              ID: {execId}
              {checkpointTs ? ` • Checkpoint: ${new Date(checkpointTs * 1000).toLocaleTimeString()}` : ''}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {(isApprovalOp || isWaiting) && !isSuccess && (
            <button
              onClick={handleApproveClick}
              disabled={isApproving}
              className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:opacity-90 text-white text-xs font-bold flex items-center gap-1.5 transition cursor-pointer shadow-md"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>{isApproving ? 'Approving...' : 'Approve Step'}</span>
            </button>
          )}

          {canResume && (
            <button
              onClick={handleResumeClick}
              disabled={isResuming}
              className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white text-xs font-bold flex items-center gap-1.5 transition cursor-pointer shadow-[0_0_15px_rgba(255,109,0,0.35)]"
            >
              <Repeat className="h-3.5 w-3.5" />
              <span>{isResuming ? 'Resuming...' : 'Resume Execution'}</span>
            </button>
          )}

          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-white/10 transition text-white/60 hover:text-white text-sm font-bold"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* ── HUMAN APPROVAL REQUIRED CARD ── */}
      {isWaiting && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 space-y-3 font-sans shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h4 className="font-bold text-xs text-white flex items-center gap-2">
                  ⏸ Human Approval Required
                </h4>
                <p className="text-[11px] text-amber-300/90">
                  Workflow execution is waiting for operator approval before continuing.
                </p>
              </div>
            </div>

            <button
              onClick={handleApproveClick}
              disabled={isApproving}
              className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1.5 shadow-md transition cursor-pointer"
            >
              <ShieldCheck className="h-4 w-4" />
              <span>{isApproving ? 'Approving Step & Resuming...' : 'Approve Step & Resume'}</span>
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 text-[11px] font-mono border-t border-amber-500/20">
            <div>
              <span className="text-amber-400/70 block text-[10px]">Execution:</span>
              <span className="text-white font-bold">{execId}</span>
            </div>
            <div>
              <span className="text-amber-400/70 block text-[10px]">Version:</span>
              <span className="text-white font-bold">
                {executionResult.version_number ? `v${executionResult.version_number}` : (executionResult.version_id || 'v7')}
              </span>
            </div>
            <div>
              <span className="text-amber-400/70 block text-[10px]">Trigger:</span>
              <span className="text-white font-bold capitalize">
                {executionResult.trigger_type || 'scheduled'}
              </span>
            </div>
            <div>
              <span className="text-amber-400/70 block text-[10px]">Progress:</span>
              <span className="text-white font-bold">
                {nodesExecuted} / {totalNodes} nodes
              </span>
            </div>
            <div>
              <span className="text-amber-400/70 block text-[10px]">Waiting Node:</span>
              <span className="text-amber-300 font-bold">
                Human Approval ({activeStepId || 'step_4'})
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Node Step Checklist (Interactive Step Selection) */}
      {nodeResults.length > 0 && (
        <div className="space-y-1">
          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">EXECUTION STEPS — SELECT TO INSPECT</span>
          <div className="flex flex-wrap items-center gap-2">
            {nodeResults.map((res: any, idx: number) => {
              const stepId = res.node_id || res.id || `step_${idx + 1}`;
              const isSelected = activeStepId === stepId;
              const isStepOk = res.status === 'SUCCESS' || res.status === 'COMPLETED';
              const isStepSkipped = res.status === 'SKIPPED';
              return (
                <button
                  key={idx}
                  onClick={() => setSelectedStepId(stepId)}
                  className={`px-2.5 py-1 rounded-lg border text-[11px] font-mono flex items-center gap-1.5 transition cursor-pointer ${
                    isSelected
                      ? 'ring-2 ring-primary bg-primary/20 border-primary font-bold text-foreground shadow-sm'
                      : isStepOk
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                      : isStepSkipped
                      ? 'bg-slate-400/10 border-slate-400/30 text-slate-400 hover:bg-slate-400/20'
                      : 'bg-destructive/10 border-destructive/30 text-destructive hover:bg-destructive/20'
                  }`}
                >
                  <span className="font-bold">[{stepId}]</span>
                  <span>{res.operation}</span>
                  <span className="text-[10px] opacity-75">({res.status})</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Structured Output Cards ── */}
      <div className="p-3 rounded-lg border border-border/80 bg-muted/30 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-muted-foreground uppercase text-[10px] tracking-wider">SELECTED STEP</span>
          {currentStep ? (
            <div className="flex items-center gap-2 font-mono">
              <span className="text-muted-foreground text-[10px]">[{activeStepId}]</span>
              <span className="bg-primary/10 text-primary px-2 py-0.5 rounded font-semibold text-[11px]">
                {currentOperation || activeStepId}
              </span>
            </div>
          ) : (
            <span className="text-muted-foreground italic font-mono text-[11px]">
              No step executed
            </span>
          )}
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-muted-foreground uppercase text-[10px] tracking-wider">STATUS</span>
          <span className={`font-mono px-2 py-0.5 rounded font-semibold text-[11px] ${
            !currentStep
              ? 'bg-muted text-muted-foreground'
              : currentStatus === 'SKIPPED'
              ? 'bg-slate-400/20 text-slate-300'
              : currentStepSuccess
              ? 'bg-emerald-500/10 text-emerald-400'
              : 'bg-destructive/10 text-destructive'
          }`}>
            {currentStatus || 'NO STEPS RUN'}
          </span>
        </div>

        {/* Empty State Card when 0 steps executed */}
        {(!currentStep || nodeResults.length === 0) && (
          <div className="p-4 rounded-xl bg-background/60 border border-border/60 text-muted-foreground text-center space-y-1 font-sans my-2">
            <p className="font-bold text-xs text-foreground">No step executed</p>
            <p className="text-[11px]">
              {executionResult.status === 'BLOCKED_MISSING_CONNECTION'
                ? 'Execution was blocked before running any steps due to missing OAuth connections.'
                : 'No node execution records were produced for this workflow.'}
            </p>
          </div>
        )}

        {/* ── AI-29 RETRY TELEMETRY CARD ── */}
        {(currentAttempts > 1 || isRecoveredAfterRetry || isExhaustedRetries || isRetryableError) && (
          <div className="pt-2 border-t border-border/60">
            {isRecoveredAfterRetry ? (
              <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-xs flex items-center justify-between shadow-sm">
                <div className="flex items-center gap-1.5 font-bold">
                  <Sparkles className="h-4 w-4 text-emerald-400" />
                  <span>✓ Recovered after temporary failure</span>
                </div>
                <span className="text-[11px] font-bold">Attempts: {currentAttempts} / {currentMaxAttempts}</span>
              </div>
            ) : isExhaustedRetries ? (
              <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-xs flex items-center justify-between shadow-sm">
                <div className="flex items-center gap-1.5 font-bold">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  <span>✕ Exhausted Retries</span>
                </div>
                <div className="flex items-center gap-2 text-[11px] font-bold">
                  <span>Attempts: {currentAttempts} / {currentMaxAttempts}</span>
                  <span>• Retryable: Yes</span>
                </div>
              </div>
            ) : (
              <div className="p-2 rounded-lg bg-muted/40 border border-border text-muted-foreground font-mono text-xs flex items-center justify-between">
                <span>Attempts: {currentAttempts} / {currentMaxAttempts}</span>
                <span>Retryable: {isRetryableError ? 'Yes' : 'No'}</span>
              </div>
            )}
          </div>
        )}

        {/* ── SKIPPED STEP VIEW (Generic for AI, Slack, Gmail, etc. when skipped) ── */}
        {currentStatus === 'SKIPPED' && (
          <div className="pt-2 border-t border-border/60 space-y-3 font-sans">
            <div className="p-4 rounded-xl bg-slate-500/10 border border-slate-400/30 space-y-3 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-400/20 pb-2">
                <span className="font-bold text-sm text-slate-300 flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-slate-400" /> Step skipped
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-400/20 text-slate-300 font-mono text-[10px] font-bold">
                  SKIPPED
                </span>
              </div>

              <div className="space-y-1.5 text-xs">
                <span className="text-muted-foreground font-semibold text-[10px] uppercase tracking-wider">SKIPPED REASON:</span>
                <div className="p-2.5 rounded-lg bg-background border border-border/80 text-muted-foreground font-mono text-xs leading-relaxed">
                  Reason: {skippedReasonText}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── SLACK RESULT VIEW ── */}
        {isSlackOp && currentStatus !== 'SKIPPED' && (
          <div className="pt-2 border-t border-border/60 space-y-3 font-sans">
            <div className={`p-4 rounded-xl space-y-3 shadow-sm border ${slackOk ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-destructive/5 border-destructive/20'}`}>
              <div className={`flex items-center justify-between border-b pb-2 ${slackOk ? 'border-emerald-500/20' : 'border-destructive/20'}`}>
                <span className={`font-bold text-sm flex items-center gap-2 ${slackOk ? 'text-emerald-400' : 'text-destructive'}`}>
                  <Hash className={`h-4 w-4 ${slackOk ? 'text-emerald-500' : 'text-destructive'}`} />
                  {slackOk ? 'Slack Message Posted' : 'Slack Operation Failed'}
                </span>
                <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${slackOk ? 'bg-emerald-500/20 text-emerald-300' : 'bg-destructive/20 text-destructive'}`}>
                  {slackOk ? '✓ SUCCESS (ok=true)' : '✕ FAILED'}
                </span>
              </div>

              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground font-semibold">Target Channel:</span>
                  <span className="font-mono bg-background border border-border px-2 py-0.5 rounded text-foreground font-bold">
                    {slackChannel}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground font-semibold">Message Timestamp (ts):</span>
                  <span className="font-mono text-muted-foreground text-[11px]">{slackTs}</span>
                </div>

                <div className="space-y-1 pt-1">
                  <span className="text-muted-foreground font-semibold text-[10px] uppercase tracking-wider">
                    {slackOk ? 'Posted Message Text:' : 'Error Details:'}
                  </span>
                  <div className={`p-2.5 rounded-lg bg-background border border-border/80 font-sans text-xs whitespace-pre-wrap leading-relaxed ${slackOk ? 'text-foreground' : 'text-destructive font-mono'}`}>
                    {slackOk ? slackText : (slackError || 'Slack operation failed.')}
                  </div>
                </div>

                {!slackOk && slackText && slackText !== slackError && (
                  <div className="space-y-1 pt-1">
                    <span className="text-muted-foreground font-semibold text-[10px] uppercase tracking-wider">
                      Intended Message Content:
                    </span>
                    <div className="p-2.5 rounded-lg bg-background border border-border/80 font-sans text-xs whitespace-pre-wrap leading-relaxed text-foreground">
                      {slackText}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── HUMAN APPROVAL RESULT VIEW ── */}
        {isApprovalOp && currentStatus !== 'SKIPPED' && (
          <div className="pt-2 border-t border-border/60 space-y-3 font-sans">
            <div className={`p-4 rounded-xl space-y-3 shadow-sm border ${
              currentStepSuccess
                ? 'bg-emerald-500/5 border-emerald-500/20'
                : 'bg-purple-500/5 border-purple-500/20'
            }`}>
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <span className="font-bold text-sm text-purple-400 flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-purple-400" /> Human Approval Step
                </span>
                <span className={`px-2.5 py-0.5 rounded font-mono text-[10px] font-bold ${
                  currentStepSuccess
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : 'bg-amber-500/20 text-amber-300'
                }`}>
                  {currentStepSuccess ? '✓ APPROVED' : '⏸ WAITING FOR APPROVAL'}
                </span>
              </div>

              <div className="space-y-2 text-xs">
                <p className="text-muted-foreground leading-relaxed">
                  {currentStepSuccess
                    ? 'This step was explicitly approved. Downstream workflow execution resumed cleanly.'
                    : 'Execution is paused waiting for human review. Click "Approve Step" to approve this step and resume downstream execution.'}
                </p>

                {!currentStepSuccess && (
                  <div className="pt-1">
                    <button
                      onClick={handleApproveClick}
                      disabled={isApproving}
                      className="w-full py-2 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition flex items-center justify-center gap-2 cursor-pointer shadow-md"
                    >
                      <ShieldCheck className="h-4 w-4" />
                      <span>{isApproving ? 'Approving Step & Resuming Execution...' : 'Approve Step & Resume Execution'}</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── AI RESULT VIEW ── */}
        {isAIOp && currentStatus !== 'SKIPPED' && (
          <div className="pt-2 border-t border-border/60 space-y-3 font-sans">
            <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 space-y-3 shadow-sm">
              <div className="flex items-center justify-between border-b border-primary/20 pb-2">
                <span className="font-bold text-sm text-primary flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" /> AI Generated Summary
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold">
                  ✓ {currentStatus}
                </span>
              </div>

              <div className="space-y-1.5">
                <span className="text-muted-foreground font-semibold text-[10px] uppercase tracking-wider">Summary Content:</span>
                <div className="p-3 rounded-lg bg-background border border-border/80 text-foreground text-xs leading-relaxed whitespace-pre-wrap font-sans">
                  {aiSummaryText}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── CONDITION / IF RESULT VIEW ── */}
        {isConditionOp && currentStatus !== 'SKIPPED' && (() => {
          const conditionOutput =
            currentOutput?.body && typeof currentOutput.body === 'object' && currentOutput.body !== null
              ? currentOutput.body
              : (currentOutput?.result !== undefined || currentOutput?.left !== undefined || currentOutput?.left_value !== undefined ? currentOutput : (currentOutput?.output?.body || currentOutput?.output || {}));

          const condResult = conditionOutput.result ?? currentOutput?.result ?? currentOutput?.output?.result;
          const condLeft = conditionOutput.left ?? conditionOutput.left_value ?? currentOutput?.left ?? currentOutput?.left_value;
          const condOperator = conditionOutput.operator || currentOutput?.operator || 'equals';
          const condRight = conditionOutput.right ?? conditionOutput.right_value ?? currentOutput?.right ?? currentOutput?.right_value;
          const condExecuted = conditionOutput.executed_branch || currentOutput?.executed_branch || (condResult ? (conditionOutput.true_branch || currentOutput?.true_branch || 'TRUE') : (conditionOutput.false_branch || currentOutput?.false_branch || 'FALSE'));
          const condSkipped = conditionOutput.skipped_branch || currentOutput?.skipped_branch || (condResult ? (conditionOutput.false_branch || currentOutput?.false_branch || 'FALSE') : (conditionOutput.true_branch || currentOutput?.true_branch || 'TRUE'));

          return (
            <div className="pt-2 border-t border-border/60 space-y-3 font-sans">
              <div className={`p-4 rounded-xl space-y-3 shadow-sm border ${
                condResult === true
                  ? 'bg-emerald-500/5 border-emerald-500/20'
                  : condResult === false
                  ? 'bg-amber-500/5 border-amber-500/20'
                  : 'bg-muted/10 border-border'
              }`}>
                <div className="flex items-center justify-between border-b border-border/40 pb-2">
                  <span className="font-bold text-sm text-foreground flex items-center gap-2">
                    <GitBranch className="h-4 w-4 text-primary" /> Condition Evaluation
                  </span>
                  <span className={`px-2.5 py-0.5 rounded font-mono text-[10px] font-bold ${
                    condResult === true
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : 'bg-amber-500/20 text-amber-300'
                  }`}>
                    EVALUATION RESULT: {condResult ? 'TRUE' : 'FALSE'}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-background border border-border/80 space-y-1 font-mono text-[11px]">
                    <div className="text-muted-foreground text-[10px] font-sans font-semibold">CONDITION RULE:</div>
                    <div className="text-foreground">
                      <span className="text-primary font-bold">{renderSafeValue(condLeft)}</span>
                      {' '}
                      <span className="text-amber-400 font-bold">[{condOperator}]</span>
                      {' '}
                      <span className="text-emerald-400 font-bold">{renderSafeValue(condRight)}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-1 font-sans">
                    <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 space-y-0.5">
                      <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">Executed Branch</span>
                      <div className="font-mono text-xs font-bold text-foreground">
                        {condExecuted}
                      </div>
                    </div>

                    <div className="p-2 rounded-lg bg-muted/30 border border-border/40 space-y-0.5 opacity-75">
                      <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Skipped Branch</span>
                      <div className="font-mono text-xs text-muted-foreground line-through">
                        {condSkipped}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })()}

        {/* ── LOOP / FOR-EACH RESULT VIEW ── */}
        {isLoopOp && currentStatus !== 'SKIPPED' && (
          <div className="pt-2 border-t border-border/60 space-y-3 font-sans">
            <div className="p-4 rounded-xl bg-purple-500/5 border border-purple-500/20 space-y-3 shadow-sm">
              <div className="flex items-center justify-between border-b border-purple-500/20 pb-2">
                <span className="font-bold text-sm text-purple-400 flex items-center gap-2">
                  <Repeat className="h-4 w-4 text-purple-400" /> Loop Iteration Summary
                </span>
                <span className="px-2.5 py-0.5 rounded font-mono text-[10px] font-bold bg-purple-500/20 text-purple-300">
                  ✓ {currentStatus}
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-2 font-sans text-xs">
                <div className="p-2.5 rounded-lg bg-background border border-border/80 text-center">
                  <div className="text-[10px] text-muted-foreground uppercase font-semibold">Total Items</div>
                  <div className="text-sm font-bold font-mono text-foreground">{currentOutput.total_items ?? currentOutput.items_processed ?? currentOutput.iterations?.length ?? 0}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                  <div className="text-[10px] text-emerald-400 uppercase font-semibold">Completed</div>
                  <div className="text-sm font-bold font-mono text-emerald-400">{currentOutput.completed_items ?? currentOutput.success_count ?? (currentOutput.iterations?.filter((it: any) => it.status !== 'FAILED').length) ?? 0}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-destructive/10 border border-destructive/20 text-center">
                  <div className="text-[10px] text-destructive uppercase font-semibold">Failed</div>
                  <div className="text-sm font-bold font-mono text-destructive">{currentOutput.failed_items ?? currentOutput.failed_count ?? (currentOutput.iterations?.filter((it: any) => it.status === 'FAILED').length) ?? 0}</div>
                </div>
              </div>

              {/* Iteration Details */}
              {Array.isArray(currentOutput.iterations) && currentOutput.iterations.length > 0 && (
                <div className="space-y-2 pt-1">
                  <span className="text-muted-foreground font-semibold text-[10px] uppercase tracking-wider">Iterations Breakdown:</span>
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {currentOutput.iterations.map((iter: any, idx: number) => (
                      <div key={idx} className="p-2.5 rounded-lg bg-background border border-border/80 space-y-1 font-mono text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-primary text-[11px]">Iteration #{idx + 1}</span>
                          <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${iter.status === 'FAILED' ? 'bg-destructive/20 text-destructive' : 'bg-emerald-500/20 text-emerald-300'}`}>
                            {iter.status || 'COMPLETED'}
                          </span>
                        </div>
                        {iter.item && (
                          <div className="text-[11px] text-muted-foreground truncate">
                            Item: {typeof iter.item === 'object' ? (iter.item.snippet || iter.item.subject || iter.item.name || iter.item.id || JSON.stringify(iter.item)) : String(iter.item)}
                          </div>
                        )}
                        {iter.output && (
                          <div className="p-1.5 rounded bg-muted/20 text-[10px] text-foreground font-sans">
                            Output: {typeof iter.output === 'object' ? (iter.output.summary || iter.output.text || JSON.stringify(iter.output)) : String(iter.output)}
                          </div>
                        )}
                        {iter.error && (
                          <div className="text-[10px] text-destructive font-mono">
                            Error: {String(iter.error)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── MULTI-EMAIL RESULTS VIEW (Gmail Search/List) ── */}
        {isGmailOp && currentStatus !== 'SKIPPED' && isMultiView && (
          <div className="pt-2 border-t border-border/60 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-foreground text-sm flex items-center gap-1.5">
                <Mail className="h-4 w-4 text-primary" /> Search Results: {emailList.length} {emailList.length === 1 ? 'email' : 'emails'}
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">
                {showingText}
              </span>
            </div>

            {/* Partial Failure Notice */}
            {multiResult.failedCount > 0 && (
              <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-500 text-[10px] flex items-center justify-between font-mono">
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> ✓ {multiResult.successCount} emails loaded
                </span>
                <span className="flex items-center gap-1 font-bold">
                  <AlertTriangle className="h-3.5 w-3.5" /> ⚠ {multiResult.failedCount} emails could not be loaded
                </span>
              </div>
            )}

            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {emailList.map((emailItem, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-background border border-border/80 space-y-2 font-sans shadow-sm">
                  <div className="flex items-center justify-between border-b border-border pb-1.5">
                    <span className="font-bold text-xs text-primary font-mono">
                      Email #{idx + 1}
                    </span>
                    <span className="text-[10px] text-muted-foreground font-mono">
                      ID: {emailItem.messageId}
                    </span>
                  </div>

                  {emailItem.isDetailed ? (
                    <>
                      {/* Sender */}
                      <div className="space-y-0.5">
                        <span className="font-bold text-muted-foreground text-[9px] uppercase tracking-wider flex items-center gap-1">
                          <User className="h-3 w-3 text-primary" /> Sender:
                        </span>
                        <div className="p-1.5 rounded bg-muted/30 border border-border/60 font-mono text-[11px] text-foreground font-medium">
                          {emailItem.sender}
                        </div>
                      </div>

                      {/* Subject */}
                      <div className="space-y-0.5">
                        <span className="font-bold text-muted-foreground text-[9px] uppercase tracking-wider flex items-center gap-1">
                          <Mail className="h-3 w-3 text-primary" /> Subject:
                        </span>
                        <div className="p-1.5 rounded bg-muted/30 border border-border/60 font-semibold text-[11px] text-foreground">
                          {emailItem.subject}
                        </div>
                      </div>

                      {/* Date */}
                      <div className="space-y-0.5">
                        <span className="font-bold text-muted-foreground text-[9px] uppercase tracking-wider flex items-center gap-1">
                          <Calendar className="h-3 w-3 text-muted-foreground" /> Date:
                        </span>
                        <div className="p-1 rounded bg-muted/20 border border-border/40 font-mono text-[10px] text-muted-foreground">
                          {emailItem.date}
                        </div>
                      </div>

                      {/* Content */}
                      <div className="space-y-0.5">
                        <span className="font-bold text-muted-foreground text-[9px] uppercase tracking-wider flex items-center gap-1">
                          <FileText className="h-3 w-3 text-primary" /> Content:
                        </span>
                        <div className="p-2.5 rounded-lg bg-muted/20 border border-border/60 text-[11px] leading-relaxed text-foreground max-h-36 overflow-y-auto whitespace-pre-wrap font-sans">
                          {emailItem.content}
                        </div>
                      </div>

                      {/* Attachments Section */}
                      <AttachmentGalleryView attachments={emailItem.attachments} messageId={emailItem.messageId} />
                    </>
                  ) : (
                    /* Message Stub Rendering (e.g. gmail.messages.list stubs without headers) */
                    <div className="space-y-1.5 text-xs font-mono pt-1">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground text-[11px]">Message ID:</span>
                        <div className="flex items-center gap-1">
                          <span className="font-bold text-foreground bg-muted/40 px-2 py-0.5 rounded text-[11px]">
                            {emailItem.messageId}
                          </span>
                          <button
                            onClick={() => handleCopyId(emailItem.messageId)}
                            className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                            title="Copy Message ID"
                          >
                            {copiedId === emailItem.messageId ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
                          </button>
                        </div>
                      </div>

                      {emailItem.threadId && emailItem.threadId !== '—' && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground text-[11px]">Thread ID:</span>
                          <span className="text-muted-foreground text-[11px] font-semibold">{emailItem.threadId}</span>
                        </div>
                      )}

                      <div className="p-2 rounded-lg bg-muted/20 border border-border/40 text-[11px] text-muted-foreground leading-relaxed font-sans mt-1">
                        Detailed email content (sender, subject, body, attachments) is retrieved in the subsequent <code className="font-mono text-primary font-semibold">gmail.messages.get</code> step.
                      </div>
                    </div>
                  )}

                  {/* Message ID & Labels Footer */}
                  <div className="flex items-center justify-between pt-1 text-[10px]">
                    <div className="flex items-center gap-1">
                      <span className="text-muted-foreground">Msg ID:</span>
                      <span className="font-mono font-semibold bg-muted/50 px-1.5 py-0.5 rounded text-foreground">
                        {emailItem.messageId}
                      </span>
                    </div>
                    {emailItem.labels.length > 0 && (
                      <div className="flex gap-1 flex-wrap">
                        {emailItem.labels.map((lbl, lIdx) => (
                          <span key={lIdx} className="px-1.5 py-0.5 rounded bg-primary/10 text-primary text-[9px] font-mono">
                            {lbl}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── SINGLE EMAIL RESULT VIEW (Gmail Get/Send) ── */}
        {isGmailOp && currentStatus !== 'SKIPPED' && !isMultiView && (singleEmail.isDetailed || (singleEmail.messageId && singleEmail.messageId !== '—')) && (
          <div className="pt-2.5 border-t border-border/60 space-y-2 text-xs">
            {/* Sender / Recipient */}
            <div className="space-y-0.5">
              <span className="font-bold text-muted-foreground text-[10px] uppercase tracking-wider flex items-center gap-1">
                <User className="h-3 w-3 text-primary" /> {isGmailSendOp ? 'Recipient:' : 'Sender:'}
              </span>
              <div className="p-2 rounded bg-background border border-border font-mono text-xs text-foreground font-medium">
                {isGmailSendOp ? (singleEmail.recipient || singleEmail.sender) : singleEmail.sender}
              </div>
            </div>

            {/* Subject */}
            <div className="space-y-0.5">
              <span className="font-bold text-muted-foreground text-[10px] uppercase tracking-wider flex items-center gap-1">
                <Mail className="h-3 w-3 text-primary" /> Subject:
              </span>
              <div className="p-2 rounded bg-background border border-border font-semibold text-xs text-foreground">
                {singleEmail.subject}
              </div>
            </div>

            {/* Date */}
            <div className="space-y-0.5">
              <span className="font-bold text-muted-foreground text-[10px] uppercase tracking-wider flex items-center gap-1">
                <Calendar className="h-3 w-3 text-muted-foreground" /> Date:
              </span>
              <div className="p-1.5 rounded bg-background border border-border font-mono text-[11px] text-muted-foreground">
                {singleEmail.date}
              </div>
            </div>

            {/* Content */}
            <div className="space-y-0.5">
              <span className="font-bold text-muted-foreground text-[10px] uppercase tracking-wider flex items-center gap-1">
                <FileText className="h-3 w-3 text-primary" /> Content:
              </span>
              <div className="p-3 rounded-lg bg-background border border-border text-xs leading-relaxed text-foreground max-h-48 overflow-y-auto whitespace-pre-wrap font-sans">
                {singleEmail.content}
              </div>
            </div>

            {/* Attachments Section */}
            <AttachmentGalleryView attachments={singleEmail.attachments} messageId={singleEmail.messageId} />

            {/* Message ID */}
            <div className="flex items-center justify-between pt-1">
              <span className="font-bold text-muted-foreground text-[10px] uppercase tracking-wider flex items-center gap-1">
                <Hash className="h-3 w-3 text-muted-foreground" /> Message ID:
              </span>
              <div className="flex items-center gap-1">
                <span className="font-mono text-foreground font-semibold bg-background px-2 py-0.5 rounded border border-border text-[11px]">
                  {singleEmail.messageId}
                </span>
                <button
                  onClick={() => handleCopyId(singleEmail.messageId)}
                  className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                  title="Copy Message ID"
                >
                  {copiedId === singleEmail.messageId ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
                </button>
              </div>
            </div>

            {/* Thread ID */}
            {singleEmail.threadId && singleEmail.threadId !== '—' && (
              <div className="flex items-center justify-between">
                <span className="font-bold text-muted-foreground text-[10px] uppercase tracking-wider flex items-center gap-1">
                  <Hash className="h-3 w-3 text-muted-foreground" /> Thread ID:
                </span>
                <span className="font-mono text-muted-foreground text-[11px]">{singleEmail.threadId}</span>
              </div>
            )}

            {/* Labels */}
            {singleEmail.labels.length > 0 && (
              <div className="flex items-center justify-between">
                <span className="font-bold text-muted-foreground text-[10px] uppercase tracking-wider flex items-center gap-1">
                  <Tag className="h-3 w-3 text-muted-foreground" /> Labels:
                </span>
                <div className="flex flex-wrap gap-1">
                  {singleEmail.labels.map((label, idx) => (
                    <span key={idx} className="px-1.5 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-mono font-medium">
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── GMAIL SEARCH EMPTY RESULT CARD (Only for Gmail list/search with 0 results) ── */}
        {isGmailOp && currentStatus !== 'SKIPPED' && isListOrSearch && emailList.length === 0 && (
          <div className="pt-2 border-t border-border/60 space-y-3 font-sans">
            <div className="p-6 rounded-xl bg-background border border-border/80 text-center space-y-3 shadow-sm">
              <div className="mx-auto w-10 h-10 rounded-full bg-muted/50 border border-border flex items-center justify-center text-muted-foreground">
                <Mail className="h-5 w-5 opacity-60" />
              </div>
              
              <div className="space-y-1">
                <h4 className="font-bold text-sm text-foreground">No matching emails found.</h4>
                <p className="text-xs text-muted-foreground font-sans">
                  Your Gmail search completed successfully but returned 0 messages.
                </p>
              </div>

              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-[11px] font-medium">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Search completed successfully • 0 results</span>
              </div>
            </div>

            {/* Expandable Raw Execution Data */}
            <details className="text-[10px] font-mono text-muted-foreground pt-1 border-t border-border/40">
              <summary className="cursor-pointer hover:text-foreground select-none py-1 font-semibold flex items-center gap-1">
                <FileText className="h-3 w-3" /> View Raw Execution Data
              </summary>
              <div className="mt-2">
                {renderSafeValue(currentOutput)}
              </div>
            </details>
          </div>
        )}

        {/* ── GENERIC / FALLBACK STEP RESULT VIEW ── */}
        {!isSlackOp && !isAIOp && !isConditionOp && currentStatus !== 'SKIPPED' && !(isGmailOp && (isMultiView || singleEmail.isDetailed || isListOrSearch)) && (
          <div className="pt-2 border-t border-border/60 space-y-2 font-mono text-xs">
            <span className="font-bold text-muted-foreground uppercase text-[10px] tracking-wider font-sans">STEP RESPONSE PAYLOAD</span>
            {renderSafeValue(currentOutput)}
          </div>
        )}
      </div>
    </div>
  );
};

// ── React Error Boundary Wrapper ───────────────────────────────────────────
export class ExecutionErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('[ExecutionErrorBoundary] Caught rendering error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-xs space-y-2 font-mono">
          <div className="flex items-center gap-2 font-bold">
            <AlertCircle className="h-4 w-4" />
            <span>Execution Output Rendering Error</span>
          </div>
          <p className="text-[11px] opacity-90">
            {this.state.error?.message || 'An unexpected rendering error occurred while displaying execution results.'}
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}

export const ExecutionResultInspector: React.FC<ExecutionResultInspectorProps> = (props) => {
  return (
    <ExecutionErrorBoundary>
      <ExecutionResultInspectorInner {...props} />
    </ExecutionErrorBoundary>
  );
};
