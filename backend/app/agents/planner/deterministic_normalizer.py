import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger("agentflow.agents.planner.deterministic_normalizer")


class DeterministicNormalizer:
    """
    Sprint AI-33: Deterministic Normalizer for AgentFlow Workflow Generation.
    Enforces Precedence Hierarchy, Negative Constraints, Entity Precedence,
    and DAG Structure Normalization post-planner V4 / decomposer.
    """

    PROHIBITED_PROVIDER_PATTERNS = {
        "slack": [
            r"do\s+not\s+(?:send|post|message|notify).*(?:slack|channel)",
            r"don\'t\s+(?:send|post|message|notify).*(?:slack|channel)",
            r"never\s+(?:send|post|message|notify).*(?:slack|channel)",
            r"no\s+slack",
            r"do\s+not\s+use\s+slack",
            r"without\s+slack",
        ],
        "gmail_send": [
            r"do\s+not\s+send\s+(?:any\s+)?email",
            r"don\'t\s+send\s+(?:any\s+)?email",
            r"never\s+send\s+(?:any\s+)?email",
            r"do\s+not\s+email",
            r"don\'t\s+email",
            r"no\s+email",
            r"without\s+emailing",
        ],
        "google_drive": [
            r"do\s+not\s+(?:upload|save).*(?:drive|google drive)",
            r"don\'t\s+(?:upload|save).*(?:drive|google drive)",
            r"no\s+drive",
        ]
    }

    def extract_prohibited_targets(self, prompt: str) -> List[str]:
        if not prompt:
            return []
        p_lower = prompt.lower().strip()
        prohibited = []

        for provider_key, patterns in self.PROHIBITED_PROVIDER_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, p_lower):
                    prohibited.append(provider_key)
                    break
        return prohibited

    def extract_slack_channel(self, prompt: str) -> Optional[str]:
        if not prompt:
            return None
        # Match explicit #channel-name
        m1 = re.search(r'#([\w-]+)', prompt)
        if m1:
            return m1.group(0)

        # Match "to <channel-name> on Slack" or "channel <channel-name>"
        m2 = re.search(r'(?:channel|to|in)\s+([a-zA-Z0-9_-]+)\s*(?:channel)?\s*(?:on\s+Slack)?', prompt, re.IGNORECASE)
        if m2:
            candidate = m2.group(1).strip()
            if candidate.lower() not in ["slack", "the", "a", "an", "email", "gmail", "message", "summary", "user", "channel"]:
                return f"#{candidate}" if not candidate.startswith("#") else candidate
        return None

    def normalize_workflow_graph(self, prompt: str, workflow_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main post-planning normalization entrypoint.
        Modifies workflow_graph in place or returns sanitized graph.
        """
        if not workflow_graph or "nodes" not in workflow_graph:
            return workflow_graph

        p_lower = prompt.lower().strip() if prompt else ""
        prohibited = self.extract_prohibited_targets(prompt)
        logger.info(f"[AI-33][NORMALIZER] Prohibited targets: {prohibited}")

        nodes = workflow_graph.get("nodes", [])
        edges = workflow_graph.get("edges", [])

        # 1. Filter out prohibited nodes
        filtered_nodes = []
        removed_node_ids = set()

        for node in nodes:
            provider = (node.get("provider") or "").lower()
            operation = (node.get("operation") or node.get("operation_id") or "").lower()

            remove = False
            if "slack" in prohibited and ("slack" in provider or "slack" in operation):
                remove = True
            if "gmail_send" in prohibited and (operation == "gmail.messages.send" or (provider == "gmail" and "send" in operation)):
                remove = True
            if "google_drive" in prohibited and ("drive" in provider or "drive" in operation):
                remove = True

            if remove:
                logger.info(f"[AI-33][NORMALIZER] Removing prohibited node: id={node.get('id')} provider={provider} op={operation}")
                removed_node_ids.add(node.get("id"))
            else:
                filtered_nodes.append(node)

        # 2. Re-stitch edges if nodes were removed
        if removed_node_ids:
            filtered_edges = []
            for edge in edges:
                src = edge.get("source")
                tgt = edge.get("target")
                if src in removed_node_ids or tgt in removed_node_ids:
                    continue
                filtered_edges.append(edge)
            workflow_graph["nodes"] = filtered_nodes
            workflow_graph["edges"] = filtered_edges
        else:
            workflow_graph["nodes"] = filtered_nodes

        # 3. Entity & Parameter Precedence Normalization
        explicit_channel = self.extract_slack_channel(prompt)
        for node in workflow_graph.get("nodes", []):
            prov = (node.get("provider") or "").lower()
            params = node.get("parameters", {})

            # Slack channel and text override if explicit values in prompt
            if "slack" in prov or node.get("operation") == "slack.chat.postMessage":
                if explicit_channel:
                    params["channel"] = explicit_channel
                    logger.info(f"[AI-33][NORMALIZER] Overrode Slack channel to '{explicit_channel}' based on prompt")
                curr_text = str(params.get("text") or "").strip()
                if not curr_text or curr_text == prompt.strip():
                    from app.agents.planner.slack_parameter_extractor import extract_slack_text
                    extracted_text = extract_slack_text(prompt)
                    if extracted_text and extracted_text != prompt.strip():
                        params["text"] = extracted_text
                        logger.info(f"[AI-33][NORMALIZER] Refined Slack text to '{extracted_text}'")

            # Email recipient override if explicitly in prompt
            if node.get("operation") == "gmail.messages.send":
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', prompt)
                if email_match:
                    params["to"] = email_match.group(0)

        return workflow_graph


deterministic_normalizer = DeterministicNormalizer()
