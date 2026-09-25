export interface NormalizedSlackResult {
  slackResult: any;
  slackChannel: string;
  slackTs: string;
  slackText: string;
  slackOk: boolean;
  slackError?: string;
}

/**
 * Normalizes Slack execution outputs to extract nested results reliably.
 * HMR-safe utility function isolated from React component exports.
 */
export function extractSlackResultDetails(
  currentOutput: any,
  currentStepSuccess: boolean = true,
  currentStep: any = null
): NormalizedSlackResult {
  const reqObj =
    currentOutput?.request?.payload ||
    currentOutput?.request?.parameters ||
    currentOutput?.request ||
    currentOutput?.parameters ||
    currentStep?.parameters ||
    currentStep?.request ||
    {};

  const slackResult =
    currentOutput?.result ??
    currentOutput?.output?.result ??
    currentOutput?.output ??
    currentOutput?.body?.result ??
    currentOutput?.body ??
    currentOutput?.response?.body ??
    currentOutput?.response ??
    currentOutput ??
    {};

  const rawReqChannel = reqObj?.channel || currentOutput?.channel || currentStep?.parameters?.channel;
  const rawResChannel = slackResult?.channel || currentOutput?.channel;

  const resolveChannel = (): string => {
    // 1. Prefer explicit request channel (e.g. "#all-agentflow-ai" or "all-agentflow-ai")
    if (typeof rawReqChannel === 'string' && rawReqChannel.trim()) {
      const trimmed = rawReqChannel.trim();
      if (trimmed.startsWith('#')) return trimmed;
      if (!/^[A-Z0-9]{8,14}$/i.test(trimmed)) {
        return `#${trimmed}`;
      }
      return trimmed;
    }

    // 2. Response / result channel (e.g. "#all-agentflow-ai" or raw ID "C0C1G4X71K6")
    if (typeof rawResChannel === 'string' && rawResChannel.trim()) {
      const trimmed = rawResChannel.trim();
      if (trimmed.startsWith('#')) return trimmed;
      if (!/^[A-Z0-9]{8,14}$/i.test(trimmed)) {
        return `#${trimmed}`;
      }
      // If raw Slack ID (e.g. C0C1G4X71K6), return ID as-is (never fallback to #general)
      return trimmed;
    }

    return '—';
  };

  const slackChannel = resolveChannel();

  const slackTs =
    slackResult?.ts ||
    slackResult?.message?.ts ||
    currentOutput?.ts ||
    '—';

  const slackOk =
    Boolean(currentStepSuccess) &&
    slackResult?.ok !== false &&
    currentOutput?.ok !== false &&
    currentOutput?.success !== false;

  const slackError =
    slackResult?.error ||
    currentOutput?.error ||
    currentStep?.error ||
    (typeof slackResult?.message === 'string' ? slackResult.message : null) ||
    'Slack operation failed.';

  const slackText =
    slackResult?.message?.text ||
    slackResult?.text ||
    reqObj?.text ||
    currentOutput?.text ||
    (!slackOk ? slackError : '—');

  return {
    slackResult,
    slackChannel,
    slackTs,
    slackText,
    slackOk,
    slackError: !slackOk ? slackError : undefined,
  };
}
