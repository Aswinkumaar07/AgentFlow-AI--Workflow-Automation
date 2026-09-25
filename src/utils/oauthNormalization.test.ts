import { normalizeAccountLabel } from './oauthReadiness';

export function runSlackNormalizationTests() {
  console.log('--- Running Slack Account Label Normalization Unit Tests ---');
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

  // Test 1: "slack_T0C1CDF...@slack.com" -> "Slack Workspace"
  const test1 = normalizeAccountLabel('Slack', 'slack_T0C1CDF1234@slack.com');
  assert(test1 === 'Slack Workspace', 'Test 1: Synthetic slack_T0C1CDF... ID email yields "Slack Workspace"');

  // Test 2: "slack_workspace@slack.com" -> "Slack Workspace"
  const test2 = normalizeAccountLabel('Slack', 'slack_workspace@slack.com');
  assert(test2 === 'Slack Workspace', 'Test 2: Generic synthetic slack_workspace@slack.com yields "Slack Workspace"');

  // Test 3: "AgentFlow Workspace" -> "AgentFlow Workspace"
  const test3 = normalizeAccountLabel('Slack', 'AgentFlow Workspace');
  assert(test3 === 'AgentFlow Workspace', 'Test 3: Custom/truthful workspace name "AgentFlow Workspace" remains unchanged');

  // Test 4: "aswinkumaar07@gmail.com" -> unchanged
  const test4 = normalizeAccountLabel('Google', 'aswinkumaar07@gmail.com');
  assert(test4 === 'aswinkumaar07@gmail.com', 'Test 4: Google email "aswinkumaar07@gmail.com" remains unchanged');

  // Test 5: undefined / empty value -> existing fallback behavior preserved
  const test5a = normalizeAccountLabel('Slack', undefined);
  assert(test5a === undefined, 'Test 5a: undefined label returns undefined');

  const test5b = normalizeAccountLabel('Slack', '');
  assert(test5b === '', 'Test 5b: empty string label returns empty string');

  console.log(`--- SUCCESS: All ${passed}/${total} Slack normalization unit tests passed! ---`);
  return { passed, total };
}

runSlackNormalizationTests();
