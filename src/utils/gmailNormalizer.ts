export interface ExtractedAttachment {
  attachmentId?: string;
  filename: string;
  mimeType: string;
  size: number;
  contentId?: string;
  disposition: 'inline' | 'attachment';
  isInline: boolean;
  isImage: boolean;
  isPdf: boolean;
  isDocument: boolean;
  data?: string;
  available?: boolean;
  downloadAvailable?: boolean;
  error?: string;
}

export interface ExtractedEmailDetails {
  messageId: string;
  threadId: string;
  sender: string;
  recipient?: string;
  subject: string;
  date: string;
  content: string;
  labels: string[];
  isDetailed: boolean;
  attachments: ExtractedAttachment[];
  inlineImages: ExtractedAttachment[];
}

export function formatFileSize(bytes: number): string {
  if (!bytes || bytes <= 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Robust Gmail base64url decoder.
 * Handles -, _, padding =, and UTF-8 string conversion.
 */
export function decodeBase64Url(base64Url: string): string {
  if (!base64Url || typeof base64Url !== 'string') return '';
  try {
    let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4 !== 0) {
      base64 += '=';
    }
    const binary = atob(base64);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    return new TextDecoder('utf-8').decode(bytes);
  } catch {
    try {
      return atob(base64Url.replace(/-/g, '+').replace(/_/g, '/'));
    } catch {
      return base64Url;
    }
  }
}

/**
 * Strips HTML tags and decodes HTML entities for plain text display.
 */
export function stripHtmlTags(html: string): string {
  if (!html || typeof html !== 'string') return '';
  return html
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/\n\s*\n/g, '\n\n')
    .trim();
}

/**
 * Recursively walks payload parts to extract text/plain or text/html content.
 */
function extractBodyFromPayload(payload: any): string {
  if (!payload) return '';

  // CASE A: Simple plain-text or HTML body at root payload
  if (payload.body && payload.body.data) {
    const rawData = decodeBase64Url(payload.body.data);
    const mimeType = String(payload.mimeType || '').toLowerCase();
    if (mimeType.includes('html')) {
      return stripHtmlTags(rawData) || rawData;
    }
    return rawData;
  }

  // CASE B & C: Multipart / Alternative / Nested Parts
  if (Array.isArray(payload.parts) && payload.parts.length > 0) {
    let textPlainPart = '';
    let textHtmlPart = '';

    const walkParts = (parts: any[]) => {
      for (const part of parts) {
        if (!part) continue;
        const mimeType = String(part.mimeType || '').toLowerCase();

        if (part.body && part.body.data) {
          const decoded = decodeBase64Url(part.body.data);
          if (mimeType === 'text/plain' && !textPlainPart) {
            textPlainPart = decoded;
          } else if (mimeType === 'text/html' && !textHtmlPart) {
            textHtmlPart = stripHtmlTags(decoded) || decoded;
          }
        }

        if (Array.isArray(part.parts) && part.parts.length > 0) {
          walkParts(part.parts);
        }
      }
    };

    walkParts(payload.parts);

    if (textPlainPart) return textPlainPart.trim();
    if (textHtmlPart) return textHtmlPart.trim();
  }

  return '';
}

const IMAGE_MIME_TYPES = new Set(['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']);
const DOCUMENT_MIME_TYPES = new Set([
  'application/pdf',
  'text/plain',
  'text/csv',
  'application/json',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/zip',
]);

/**
 * Recursively walks nested Gmail payload tree to extract attachments and inline images in frontend JS/TS.
 */
export function extractAttachmentsFromPayload(msg: any): {
  attachments: ExtractedAttachment[];
  inlineImages: ExtractedAttachment[];
} {
  const attachments: ExtractedAttachment[] = [];
  const inlineImages: ExtractedAttachment[] = [];
  const seenKeys = new Set<string>();

  const msgId = String(msg.id || msg.messageId || 'unknown');
  const payload = msg.payload || msg.body?.payload || msg;

  const walkPart = (part: any) => {
    if (!part || typeof part !== 'object') return;

    const filename = String(part.filename || '').trim();
    const mimeType = String(part.mimeType || '').trim().toLowerCase();
    const body = part.body || {};
    const attachmentId = String(body.attachmentId || part.attachmentId || '').trim();
    const size = Number(body.size || part.size || 0);
    const rawB64Data = body.data || part.data || '';

    const headers = Array.isArray(part.headers) ? part.headers : [];
    let contentDisposition = '';
    let contentId = '';

    for (const h of headers) {
      if (!h || typeof h !== 'object') continue;
      const hName = String(h.name || '').toLowerCase();
      const hVal = String(h.value || '');
      if (hName === 'content-disposition') {
        contentDisposition = hVal;
      } else if (hName === 'content-id') {
        contentId = hVal.replace(/^<|>$ /g, '').trim();
      }
    }

    const isContainer = ['multipart/mixed', 'multipart/alternative', 'multipart/related', 'multipart/digest'].includes(mimeType);
    const isNormalBody = ['text/plain', 'text/html'].includes(mimeType) && !filename && !attachmentId && !contentId;

    if (!isContainer && !isNormalBody) {
      const isInline = contentDisposition.toLowerCase().includes('inline') || Boolean(contentId);
      const isImage = IMAGE_MIME_TYPES.has(mimeType) || mimeType.startsWith('image/');
      const isPdf = mimeType === 'application/pdf';
      const isDocument = DOCUMENT_MIME_TYPES.has(mimeType) || isPdf || mimeType.startsWith('text/');

      const uniqueKey = attachmentId || contentId || `${filename}_${size}_${mimeType}`;

      if (!seenKeys.has(uniqueKey) && (filename || attachmentId || isImage || contentId)) {
        seenKeys.add(uniqueKey);

        const cleanName = filename || (attachmentId ? `attachment_${attachmentId.slice(0, 8)}.bin` : 'file.bin');

        let dataUrl: string | undefined = undefined;
        if (rawB64Data) {
          const rawText = decodeBase64Url(rawB64Data);
          if (rawText) {
            try {
              let cleanB64 = rawB64Data.replace(/-/g, '+').replace(/_/g, '/');
              while (cleanB64.length % 4 !== 0) cleanB64 += '=';
              dataUrl = `data:${mimeType || 'application/octet-stream'};base64,${cleanB64}`;
            } catch {
              // ignore
            }
          }
        } else if (attachmentId) {
          dataUrl = `/api/v1/gmail/messages/${msgId}/attachments/${attachmentId}?filename=${encodeURIComponent(cleanName)}&mime_type=${encodeURIComponent(mimeType)}`;
        }

        const maxLimit = 10 * 1024 * 1024;
        const attObj: ExtractedAttachment = {
          attachmentId: attachmentId || undefined,
          filename: cleanName,
          mimeType: mimeType || 'application/octet-stream',
          size: size,
          contentId: contentId || undefined,
          disposition: isInline ? 'inline' : 'attachment',
          isInline: isInline,
          isImage: isImage,
          isPdf: isPdf,
          isDocument: isDocument,
          data: dataUrl,
          available: size <= maxLimit,
          downloadAvailable: size <= maxLimit,
          error: size > maxLimit ? 'Attachment exceeds maximum size limit of 10 MB' : undefined,
        };

        if (isInline || (isImage && contentId)) {
          inlineImages.push(attObj);
        } else {
          attachments.push(attObj);
        }
      }
    }

    if (Array.isArray(part.parts)) {
      for (const subpart of part.parts) {
        walkPart(subpart);
      }
    }
  };

  walkPart(payload);
  return { attachments, inlineImages };
}

/**
 * Normalizes any single Gmail API message response into structured email details.
 */
export function extractGmailMessageDetails(inputData: any): ExtractedEmailDetails {
  let msg = inputData;
  if (!msg) {
    return {
      messageId: '—',
      threadId: '—',
      sender: 'Unknown Sender',
      subject: '(No Subject)',
      date: '—',
      content: 'No message content available.',
      labels: [],
      isDetailed: false,
      attachments: [],
      inlineImages: [],
    };
  }

  // Preserve references to raw input and step before unwrapping
  let targetStep = inputData;
  if (Array.isArray(msg.node_results) && msg.node_results.length > 0) {
    const getStep = msg.node_results.slice().reverse().find((r: any) =>
      r.operation === 'gmail.messages.get' || r.operation === 'gmail.get' || r.output?.body?.payload || r.output?.response?.payload
    );
    targetStep = getStep || msg.node_results[msg.node_results.length - 1];
    msg = targetStep.output || targetStep;
  }

  // Extract request payload if present (e.g. for gmail.messages.send or parameters)
  const reqPayload =
    targetStep?.output?.request?.payload ||
    targetStep?.request?.payload ||
    targetStep?.parameters ||
    targetStep?.output?.parameters ||
    targetStep?.output?.payload ||
    targetStep?.payload ||
    inputData?.output?.request?.payload ||
    inputData?.request?.payload ||
    inputData?.parameters ||
    inputData?.output?.parameters ||
    msg?.output?.request?.payload ||
    msg?.request?.payload ||
    msg?.parameters ||
    null;

  // Unwrap common nested response shapes
  if (msg.output) msg = msg.output;
  if (msg.body) msg = msg.body;
  if (msg.response) msg = msg.response;
  if (msg.body) msg = msg.body;

  // Extract ID / Thread / Labels
  const messageId = String(msg.id || msg.messageId || '');
  const threadId = String(msg.threadId || '');
  const labels: string[] = Array.isArray(msg.labelIds) ? msg.labelIds : [];

  // Extract Headers (case-insensitive From, Subject, Date)
  const headers = msg.payload?.headers || msg.headers || [];
  let sender = '';
  let subject = '';
  let date = '';

  if (Array.isArray(headers)) {
    for (const h of headers) {
      if (!h || !h.name) continue;
      const nameLower = String(h.name).toLowerCase();
      if (nameLower === 'from' && !sender) sender = String(h.value || '');
      if (nameLower === 'subject' && !subject) subject = String(h.value || '');
      if (nameLower === 'date' && !date) date = String(h.value || '');
    }
  }

  // Extract request-level values for send operations (to, subject, body)
  const rawTo = reqPayload?.to ?? reqPayload?.recipient;
  const reqTo = Array.isArray(rawTo)
    ? rawTo.join(', ')
    : rawTo
    ? String(rawTo)
    : '';
  const reqSubject = reqPayload?.subject ? String(reqPayload.subject) : '';
  const reqBody = reqPayload?.body
    ? String(reqPayload.body)
    : reqPayload?.text
    ? String(reqPayload.text)
    : reqPayload?.content
    ? String(reqPayload.content)
    : '';

  // Fallback for sender & recipient from request payload if not in headers
  const recipient = reqTo || undefined;
  if (!sender && reqTo) {
    sender = reqTo;
  }

  // Fallback for subject from request payload if not in headers
  if (!subject && reqSubject) {
    subject = reqSubject;
  }

  // Fallback for Date if missing from headers
  if (!date && msg.internalDate) {
    try {
      const ms = Number(msg.internalDate);
      if (!isNaN(ms)) {
        date = new Date(ms).toUTCString();
      }
    } catch {
      // ignore
    }
  }

  // Extract attachments & inline images using recursive walker or pre-normalized backend payload
  let attachments: ExtractedAttachment[] = [];
  let inlineImages: ExtractedAttachment[] = [];

  const rawAtts = Array.isArray(msg.attachments)
    ? msg.attachments
    : Array.isArray(msg.body?.attachments)
    ? msg.body.attachments
    : null;

  const rawInline = Array.isArray(msg.inline_images)
    ? msg.inline_images
    : Array.isArray(msg.body?.inline_images)
    ? msg.body.inline_images
    : null;

  if (rawAtts !== null || rawInline !== null) {
    attachments = (rawAtts || []).map((att: any) => ({
      attachmentId: att.attachment_id || att.attachmentId,
      filename: String(att.filename || 'attachment.bin'),
      mimeType: String(att.mime_type || att.mimeType || 'application/octet-stream').toLowerCase(),
      size: Number(att.size || att.size_bytes || 0),
      contentId: att.content_id || att.contentId,
      disposition: att.disposition || (att.is_inline ? 'inline' : 'attachment'),
      isInline: Boolean(att.is_inline || att.isInline),
      isImage: Boolean(att.is_image || att.isImage),
      isPdf: Boolean(att.is_pdf || att.isPdf),
      isDocument: Boolean(att.is_document || att.isDocument),
      data: att.data,
      available: att.available !== false,
      downloadAvailable: att.download_available !== false,
      error: att.error,
    }));

    inlineImages = (rawInline || []).map((att: any) => ({
      attachmentId: att.attachment_id || att.attachmentId,
      filename: String(att.filename || 'inline_image.png'),
      mimeType: String(att.mime_type || att.mimeType || 'image/png').toLowerCase(),
      size: Number(att.size || att.size_bytes || 0),
      contentId: att.content_id || att.contentId,
      disposition: 'inline',
      isInline: true,
      isImage: true,
      isPdf: false,
      isDocument: false,
      data: att.data,
      available: att.available !== false,
      downloadAvailable: att.download_available !== false,
      error: att.error,
    }));
  } else {
    const extracted = extractAttachmentsFromPayload(msg);
    attachments = extracted.attachments;
    inlineImages = extracted.inlineImages;
  }

  // Extract Body Content
  let content = extractBodyFromPayload(msg.payload || msg);

  if (!content && typeof msg.snippet === 'string' && msg.snippet.trim()) {
    content = msg.snippet.trim();
  }

  if (!content && inlineImages.length > 0) {
    const names = inlineImages.map((img) => img.filename).join(', ');
    content = `[Inline Image Content: ${names}]`;
  }

  // Fallback for Body Content from request payload for send operations
  if ((!content || content === 'No message content available.') && reqBody) {
    content = reqBody;
  }

  if (!content) {
    content = 'No message content available.';
  }

  const isDetailed = Boolean(sender || subject || (msg.payload && msg.payload.headers));

  return {
    messageId: messageId || '—',
    threadId: threadId || '—',
    sender: sender || 'Unknown Sender',
    recipient: recipient,
    subject: subject || '(No Subject)',
    date: date || '—',
    content: content,
    labels: labels,
    isDetailed: isDetailed,
    attachments: attachments,
    inlineImages: inlineImages,
  };
}

/**
 * Extracts multiple normalized emails from a multi-message or fan-out result object.
 */
export function extractMultipleGmailMessageDetails(inputData: any): {
  emails: ExtractedEmailDetails[];
  totalCount: number;
  successCount: number;
  failedCount: number;
} {
  if (!inputData) {
    return { emails: [], totalCount: 0, successCount: 0, failedCount: 0 };
  }

  let targetOutput = inputData;
  if (Array.isArray(inputData.node_results) && inputData.node_results.length > 0) {
    const getStep = inputData.node_results.slice().reverse().find((r: any) =>
      r.operation === 'gmail.messages.get' || r.output?.messages || r.output?.body?.messages || r.output?.items
    );
    const targetStep = getStep || inputData.node_results[inputData.node_results.length - 1];
    targetOutput = targetStep.output || targetStep;
  }

  if (targetOutput.output) targetOutput = targetOutput.output;
  if (targetOutput.body) targetOutput = targetOutput.body;
  if (targetOutput.response) targetOutput = targetOutput.response;
  if (targetOutput.body) targetOutput = targetOutput.body;

  const rawList: any[] = Array.isArray(targetOutput.messages)
    ? targetOutput.messages
    : Array.isArray(targetOutput.items)
    ? targetOutput.items
    : Array.isArray(targetOutput.data?.messages)
    ? targetOutput.data.messages
    : [];

  const emails: ExtractedEmailDetails[] = [];
  let successCount = 0;
  let failedCount = typeof targetOutput.failed_count === 'number' ? targetOutput.failed_count : 0;

  for (const item of rawList) {
    const details = extractGmailMessageDetails(item);
    if (details.messageId && details.messageId !== '—') {
      emails.push(details);
      successCount++;
    } else {
      failedCount++;
    }
  }

  const totalCount = typeof targetOutput.total_items === 'number' ? targetOutput.total_items : emails.length;

  return {
    emails,
    totalCount: totalCount || emails.length,
    successCount: typeof targetOutput.success_count === 'number' ? targetOutput.success_count : successCount,
    failedCount,
  };
}
