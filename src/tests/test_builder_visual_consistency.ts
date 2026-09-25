import { useWorkflowStore } from '../store/useWorkflowStore';
import type { AIGenerateResponse } from '../types/ai';

export function testWorkflowStoreParameterMapping(): void {
  const store = useWorkflowStore.getState();

  const mockResponse: AIGenerateResponse = {
    user_prompt: "Find my open GitHub issues, summarize them using AI, and send the summary to #all-agentflow-ai on Slack.",
    goal: "GitHub to Slack summary",
    services: ["github", "ai", "slack"],
    workflow_json: {
      title: "GitHub to Slack summary",
      description: "Find issues, summarize, and post to Slack",
      nodes: [
        {
          id: "step_1",
          provider: "github",
          operation_id: "github.issues.search",
          parameters: {
            q: "is:issue state:open",
            auth_provider: "Github",
            credential_id: null,
            auth_account_label: null,
            auth_status: "unbound",
          },
          data: {
            label: "Search GitHub Issues",
            provider: "github",
            operation_id: "github.issues.search",
            step_id: "step_1",
          },
        },
        {
          id: "step_2",
          provider: "ai",
          operation_id: "ai.summarize",
          parameters: {
            text: "{{step_1.items}}",
            auth_provider: "Ai",
            credential_id: null,
            auth_account_label: null,
            auth_status: "unbound",
          },
          data: {
            label: "AI Summarize",
            provider: "ai",
            operation_id: "ai.summarize",
            step_id: "step_2",
          },
        },
        {
          id: "step_3",
          provider: "slack",
          operation_id: "slack.chat.postMessage",
          parameters: {
            channel: "#all-agentflow-ai",
            text: "{{step_2.summary}}",
            auth_provider: "Slack",
            credential_id: null,
            auth_account_label: null,
            auth_status: "unbound",
          },
          data: {
            label: "Send Slack Summary",
            provider: "slack",
            operation_id: "slack.chat.postMessage",
            step_id: "step_3",
          },
        },
      ],
      edges: [
        { id: "e1-2", source: "step_1", target: "step_2" },
        { id: "e2-3", source: "step_2", target: "step_3" },
      ],
    },
    is_valid: true,
  };

  store.setWorkflow(mockResponse);

  const updatedNodes = useWorkflowStore.getState().nodes;
  if (updatedNodes.length !== 3) {
    throw new Error(`Expected 3 nodes, got ${updatedNodes.length}`);
  }

  const githubNode = updatedNodes.find((n) => n.id === "step_1");
  const slackNode = updatedNodes.find((n) => n.id === "step_3");

  if (!githubNode || !slackNode) {
    throw new Error("Missing expected nodes in parsed workflow");
  }

  const ghParams = (githubNode.data as Record<string, any>).parameters || {};
  const slackParams = (slackNode.data as Record<string, any>).parameters || {};

  // A. Verify n.parameters is preserved in node.data.parameters
  if (ghParams.auth_status !== "unbound") {
    throw new Error("GitHub node failed to preserve parameters.auth_status = unbound");
  }

  if (slackParams.channel !== "#all-agentflow-ai") {
    throw new Error("Slack node failed to preserve parameters.channel");
  }

  if (slackParams.auth_status !== "unbound" || slackParams.credential_id !== null) {
    throw new Error("Slack node failed to preserve auth_status = unbound and credential_id = null");
  }

  console.log("✓ testWorkflowStoreParameterMapping passed cleanly");
}
