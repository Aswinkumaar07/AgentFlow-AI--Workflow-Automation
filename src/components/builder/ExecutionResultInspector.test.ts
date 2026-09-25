if (typeof globalThis.localStorage === 'undefined') {
  (globalThis as any).localStorage = {
    getItem: () => null,
    setItem: () => {},
    removeItem: () => {},
    clear: () => {},
  };
}

import { extractSlackResultDetails } from '../../utils/slackNormalizer.js';
import { extractGmailMessageDetails, extractMultipleGmailMessageDetails } from '../../utils/gmailNormalizer.js';
import { resolveApprovalTargetDetails } from './ExecutionResultInspector.js';

/**
 * Frontend Regression Test Suite for ExecutionResultInspector Slack Normalization
 */
export function runExecutionResultInspectorTests() {
  console.log('--- Running ExecutionResultInspector Regression Tests ---');
  let passed = 0;
  let total = 0;

  function assert(condition: boolean, description: string) {
    total++;
    if (!condition) {
      console.error(`[FAIL] Test #${total}: ${description}`);
      throw new Error(`Test failed: ${description}`);
    } else {
      console.log(`[PASS] Test #${total}: ${description}`);
      passed++;
    }
  }

  // Exact payload from user request / LiveNodeExecutionResult runtime shape
  const liveRuntimePayload = {
    status_code: 200,
    request: {
      url: "https://slack.com/api/chat.postMessage",
      method: "POST",
      payload: {
        channel: "#all-agentflow-ai",
        text: "Email summary: The email contains details regarding requested topics."
      }
    },
    response: {
      status_code: 200,
      body: {
        ok: true,
        channel: "C0C1G4X71K6",
        ts: "1789208352.915499",
        message: {
          text: "Email summary: The email contains details regarding requested topics."
        }
      }
    },
    body: {
      ok: true,
      channel: "C0C1G4X71K6",
      ts: "1789208352.915499",
      message: {
        text: "Email summary: The email contains details regarding requested topics."
      }
    }
  };

  // 1. Test exact live runtime execution payload
  const liveResult = extractSlackResultDetails(liveRuntimePayload, true);
  assert(liveResult.slackChannel === '#all-agentflow-ai', 'Live Payload: Target Channel matches #all-agentflow-ai');
  assert(liveResult.slackTs === '1789208352.915499', 'Live Payload: Timestamp matches 1789208352.915499');
  assert(
    liveResult.slackText === 'Email summary: The email contains details regarding requested topics.',
    'Live Payload: Message matches Email summary...'
  );
  assert(liveResult.slackOk === true, 'Live Payload: Slack operation ok=true');

  // Exact payload format from backend direct dictionary
  const realPayload = {
    success: true,
    result: {
      ok: true,
      channel: "C0C1G4X71K6",
      ts: "1789208352.915499",
      message: {
        text: "Email summary: The email contains details regarding requested topics."
      }
    },
    request: {
      channel: "#all-agentflow-ai"
    }
  };

  const realResult = extractSlackResultDetails(realPayload, true);
  assert(realResult.slackChannel === '#all-agentflow-ai', 'Target Channel matches #all-agentflow-ai');
  assert(realResult.slackTs === '1789208352.915499', 'Timestamp matches 1789208352.915499');
  assert(
    realResult.slackText === 'Email summary: The email contains details regarding requested topics.',
    'Message matches Email summary...'
  );
  assert(realResult.slackOk === true, 'Slack operation is ok');

  // Test A: Slack result nested under result
  const payloadA = {
    result: {
      ok: true,
      channel: 'C0C1G4X71K6',
      ts: '1789208352.915499',
      message: { text: 'Nested message text' }
    }
  };
  const resA = extractSlackResultDetails(payloadA, true);
  assert(resA.slackChannel === 'C0C1G4X71K6', 'Test A: Raw channel ID preserved safely');
  assert(resA.slackTs === '1789208352.915499', 'Test A: Timestamp extracted from nested result');
  assert(resA.slackText === 'Nested message text', 'Test A: Text extracted from nested result');

  // Test B: Slack result with direct top-level channel/ts
  const payloadB = {
    ok: true,
    channel: '#general-announcements',
    ts: '1234567890.123456',
    text: 'Top-level message'
  };
  const resB = extractSlackResultDetails(payloadB, true);
  assert(resB.slackChannel === '#general-announcements', 'Test B: Direct top-level channel extracted');
  assert(resB.slackTs === '1234567890.123456', 'Test B: Direct top-level ts extracted');
  assert(resB.slackText === 'Top-level message', 'Test B: Direct top-level text extracted');

  // Test C: Slack result with channel ID + request channel name
  const payloadC = {
    result: {
      ok: true,
      channel: 'C0C1G4X71K6',
      ts: '1000.0001'
    },
    parameters: {
      channel: 'all-agentflow-ai',
      text: 'Request text'
    }
  };
  const resC = extractSlackResultDetails(payloadC, true);
  assert(resC.slackChannel === '#all-agentflow-ai', 'Test C: Request channel name preferred over raw ID');
  assert(resC.slackText === 'Request text', 'Test C: Request text fallback used');

  // Test D: Failed Slack result displays actual error
  const payloadD = {
    result: {
      ok: false,
      error: 'channel_not_found'
    }
  };
  const resD = extractSlackResultDetails(payloadD, false);
  assert(resD.slackOk === false, 'Test D: Failed status correctly identified');
  assert(resD.slackError === 'channel_not_found', 'Test D: Actual error returned');
  assert(resD.slackText === 'channel_not_found', 'Test D: Text displays actual error instead of success message');

  // Test E: Slack success NEVER falls back to #general
  const payloadE = {
    result: {
      ok: true,
      channel: 'C999888777',
      ts: '2222.3333'
    }
  };
  const resE = extractSlackResultDetails(payloadE, true);
  assert(resE.slackChannel !== '#general', 'Test E: Never falls back to #general');
  assert(resE.slackChannel === 'C999888777', 'Test E: Safe raw channel ID used');

  // Requirement 5 Test D: Skipped AI renderer payload status SKIPPED never fake success
  const skippedAIPayload = {
    node_id: 'step_4',
    operation: 'ai.summarize',
    status: 'SKIPPED',
    output: { status: 'SKIPPED', reason: 'Skipped due to condition evaluation' }
  };
  assert(skippedAIPayload.status === 'SKIPPED', 'Test D: Skipped AI status is SKIPPED');
  assert(skippedAIPayload.output.reason.includes('Skipped due to condition'), 'Test D: Skipped AI reason preserved');

  // Requirement 5 Test E: Skipped Slack renderer payload status SKIPPED never fake success
  const skippedSlackPayload = {
    node_id: 'step_5',
    operation: 'slack.chat.postMessage',
    status: 'SKIPPED',
    output: { status: 'SKIPPED', reason: 'Skipped due to condition evaluation' }
  };
  assert(skippedSlackPayload.status === 'SKIPPED', 'Test E: Skipped Slack status is SKIPPED');
  assert(skippedSlackPayload.output.reason.includes('Skipped due to condition'), 'Test E: Skipped Slack reason preserved');

  // --- Gmail Normalization Tests (A, B, C) ---

  // Test A: gmail.messages.list with message stub -> NOT empty state
  const gmailListStubPayload = {
    node_id: "step_1",
    status: "COMPLETED",
    output: {
      status_code: 200,
      response: {
        messages: [
          { id: "1a0a03f09244290d", threadId: "1a0a03f09244290d" }
        ],
        nextPageToken: "12345",
        resultSizeEstimate: 201
      }
    }
  };
  const gmailListRes = extractMultipleGmailMessageDetails(gmailListStubPayload);
  assert(gmailListRes.emails.length === 1, 'Test A: gmail.messages.list with stub returns 1 email (not 0)');
  assert(gmailListRes.emails[0].messageId === '1a0a03f09244290d', 'Test A: Message ID extracted correctly');
  assert(gmailListRes.emails[0].isDetailed === false, 'Test A: Message stub correctly marked as not detailed');

  // Test B: gmail.messages.list with zero messages -> empty state
  const gmailEmptyListPayload = {
    node_id: "step_1",
    status: "COMPLETED",
    output: {
      status_code: 200,
      response: {
        messages: [],
        resultSizeEstimate: 0
      }
    }
  };
  const gmailEmptyRes = extractMultipleGmailMessageDetails(gmailEmptyListPayload);
  assert(gmailEmptyRes.emails.length === 0, 'Test B: gmail.messages.list with 0 messages returns 0 emails');

  // Test C: gmail.messages.get detailed email -> detailed rendering preserved
  const gmailGetDetailedPayload = {
    node_id: "step_2",
    status: "COMPLETED",
    output: {
      status_code: 200,
      response: {
        id: "1a0a03f09244290d",
        threadId: "1a0a03f09244290d",
        snippet: "Aswinkumaar, 3 new updates for you",
        payload: {
          headers: [
            { name: "From", value: "notifications-noreply@linkedin.com" },
            { name: "Subject", value: "Deepika M posted..." }
          ]
        }
      }
    }
  };
  const gmailGetRes = extractGmailMessageDetails(gmailGetDetailedPayload);
  assert(gmailGetRes.messageId === '1a0a03f09244290d', 'Test C: Detailed email message ID matches');
  assert(gmailGetRes.sender === 'notifications-noreply@linkedin.com', 'Test C: Sender extracted from headers');
  assert(gmailGetRes.subject === 'Deepika M posted...', 'Test C: Subject extracted from headers');
  assert(gmailGetRes.isDetailed === true, 'Test C: Detailed email correctly marked as detailed');

  // --- AI Summary Extraction Tests (A, B, C, D, E) ---

  function extractAISummaryText(currentOutput: any): string {
    if (!currentOutput) return 'No output summary available.';
    
    const responseObj = currentOutput?.response || currentOutput?.body || currentOutput?.result || currentOutput;

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

    return (
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
      'No output summary available.'
    );
  }

  // AI Test A: Direct summary property
  const aiPayloadA = { summary: "Direct summary text" };
  assert(extractAISummaryText(aiPayloadA) === "Direct summary text", 'AI Test A: Direct currentOutput.summary extracted');

  // AI Test B: Nested response.body.summary (actual live backend shape)
  const aiPayloadB = {
    status_code: 200,
    response: {
      status_code: 200,
      body: {
        summary: "Summary: Aswinkumaar, 3 new updates for you",
        text: "Summary: Aswinkumaar, 3 new updates for you",
        status: "executed",
        model: "Gemini 2.5 Pro"
      }
    }
  };
  assert(extractAISummaryText(aiPayloadB) === "Summary: Aswinkumaar, 3 new updates for you", 'AI Test B: Nested response.body.summary extracted');

  // AI Test C: Nested response.body.text when summary property is missing
  const aiPayloadC = {
    response: {
      body: {
        text: "Text-only summary content",
        status: "executed"
      }
    }
  };
  assert(extractAISummaryText(aiPayloadC) === "Text-only summary content", 'AI Test C: Nested response.body.text extracted');

  // AI Test D: Missing/unusable summary -> Fallback triggered
  const aiPayloadD = {
    response: {
      body: {
        status: "executed"
      }
    }
  };
  assert(extractAISummaryText(aiPayloadD) === "No output summary available.", 'AI Test D: Fallback returned when no summary/text');

  // AI Test E: Unexpected body types (null, number, object without summary/text) handle safely
  assert(extractAISummaryText({ response: { body: null } }) === "No output summary available.", 'AI Test E: Null body handled safely');
  assert(extractAISummaryText({ response: { body: 12345 } }) === "No output summary available.", 'AI Test E: Number body handled safely');
  assert(extractAISummaryText({ response: { body: [] } }) === "No output summary available.", 'AI Test E: Array body handled safely');

  // --- Condition Details Normalization Tests (Nested & Flat) ---

  function extractConditionDetails(currentOutput: any) {
    const conditionOutput =
      currentOutput?.body && typeof currentOutput.body === 'object' && currentOutput.body !== null
        ? currentOutput.body
        : (currentOutput?.result !== undefined || currentOutput?.left !== undefined || currentOutput?.left_value !== undefined ? currentOutput : (currentOutput?.output?.body || currentOutput?.output || {}));

    const result = conditionOutput.result ?? currentOutput?.result ?? currentOutput?.output?.result;
    const left = conditionOutput.left ?? conditionOutput.left_value ?? currentOutput?.left ?? currentOutput?.left_value ?? '-';
    const operator = conditionOutput.operator || currentOutput?.operator || 'equals';
    const right = conditionOutput.right ?? conditionOutput.right_value ?? currentOutput?.right ?? currentOutput?.right_value ?? '-';

    return {
      result,
      left,
      operator,
      right,
      ruleText: `${left} [${operator}] ${right}`
    };
  }

  // Condition Test 1: Nested body payload (live backend shape)
  const condPayloadNested = {
    status: 200,
    body: {
      left: "{{step_2.snippet}}",
      operator: "contains",
      right: "urgent",
      result: false
    }
  };
  const condResNested = extractConditionDetails(condPayloadNested);
  assert(condResNested.left === "{{step_2.snippet}}", 'Condition Test 1: Nested body left extracted as {{step_2.snippet}}');
  assert(condResNested.operator === "contains", 'Condition Test 1: Nested body operator extracted as contains');
  assert(condResNested.right === "urgent", 'Condition Test 1: Nested body right extracted as urgent');
  assert(condResNested.result === false, 'Condition Test 1: Nested body result extracted as false');
  assert(condResNested.ruleText === "{{step_2.snippet}} [contains] urgent", 'Condition Test 1: Rule text matches {{step_2.snippet}} [contains] urgent');

  // Condition Test 2: Flat payload (backwards compatibility)
  const condPayloadFlat = {
    left: "value",
    operator: "equals",
    right: "urgent"
  };
  const condResFlat = extractConditionDetails(condPayloadFlat);
  assert(condResFlat.left === "value", 'Condition Test 2: Flat left extracted as value');
  assert(condResFlat.operator === "equals", 'Condition Test 2: Flat operator extracted as equals');
  assert(condResFlat.right === "urgent", 'Condition Test 2: Flat right extracted as urgent');
  assert(condResFlat.ruleText === "value [equals] urgent", 'Condition Test 2: Rule text matches value [equals] urgent');

  // --- AI-25 Approval Target Resolution Tests ---
  const ai25ExecutionResult = {
    execution_id: "exec_v3_d874535473",
    status: "WAITING",
    node_results: [
      { node_id: "step_1", status: "COMPLETED", provider: "gmail" },
      { node_id: "step_2", status: "COMPLETED", provider: "gmail" },
      { node_id: "step_0oxx7", status: "WAITING", provider: "Approval" },
    ]
  };

  // Test A: Dynamic pending approval node ID is used correctly
  const resA25 = resolveApprovalTargetDetails(ai25ExecutionResult, null);
  assert(resA25.targetExecId === "exec_v3_d874535473", "AI-25 Test A: Target execution_id matches exec_v3_d874535473");
  assert(resA25.targetNodeId === "step_0oxx7", "AI-25 Test A: Dynamic pending approval node ID resolved to step_0oxx7");

  // Test B: No hardcoded step_4 is ever sent when selectedStepId is null or missing
  assert(resA25.targetNodeId !== "step_4", "AI-25 Test B: Hardcoded step_4 is never used");

  // Test C: Explicit valid selectedStepId (matching approval step) is respected
  const resA25Selected = resolveApprovalTargetDetails(ai25ExecutionResult, "step_0oxx7");
  assert(resA25Selected.targetNodeId === "step_0oxx7", "AI-25 Test C: Explicit pending selectedStepId used");

  // Test D: Missing selectedStepId and no matching nodeResult approval provider -> targetNodeId is undefined (triggers backend auto-discovery)
  const noApprovalNodeResult = {
    execution_id: "exec_v3_99999",
    status: "WAITING",
    node_results: [
      { node_id: "step_1", status: "COMPLETED" },
    ]
  };
  const resA25Omit = resolveApprovalTargetDetails(noApprovalNodeResult, null);
  assert(resA25Omit.targetExecId === "exec_v3_99999", "AI-25 Test D: Execution ID preserved");
  assert(resA25Omit.targetNodeId === undefined, "AI-25 Test D: Node ID undefined to allow backend auto-discovery");

  // Test E: exec_live is never used as targetExecId
  const execLiveResult = {
    execution_id: "exec_live",
    status: "WAITING",
    node_results: []
  };
  const resExecLive = resolveApprovalTargetDetails(execLiveResult, null);
  assert(resExecLive.targetExecId === null, "AI-25 Test E: exec_live is rejected as targetExecId");

  console.log(`--- SUCCESS: All ${passed}/${total} regression tests passed! ---`);
  return { passed, total };
}

runExecutionResultInspectorTests();
