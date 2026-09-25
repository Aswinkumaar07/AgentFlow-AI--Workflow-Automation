import logging
from typing import Any, Dict, List, Set
from app.agents.api_discovery.interfaces import BaseCapabilityGraph
from app.agents.api_discovery.models import APICapabilityNode

logger = logging.getLogger("agentflow.api_discovery.graph")


class CapabilityGraph(BaseCapabilityGraph):
    """Directed Capability Graph describing provider capabilities and multi-step workflow transitions."""

    def __init__(self) -> None:
        self.nodes: Dict[str, APICapabilityNode] = {}
        self.adjacency: Dict[str, List[Dict[str, str]]] = {}
        self._initialize_default_graph()

    def _initialize_default_graph(self) -> None:
        """Pre-populates enterprise capability nodes and transitions."""
        # 1. Gmail Node
        gmail_node = APICapabilityNode(
            node_id="gmail.email",
            provider="Gmail",
            entity_type="Email",
            input_types=["search_query"],
            output_types=["email_payload", "invoice_file"],
            operations=["gmail.messages.list", "gmail.attachments.get"],
        )
        self.add_node(gmail_node)

        # 2. Drive Node
        drive_node = APICapabilityNode(
            node_id="drive.storage",
            provider="Google Drive",
            entity_type="Document",
            input_types=["invoice_file", "document"],
            output_types=["file_link"],
            operations=["drive.files.create"],
        )
        self.add_node(drive_node)

        # 3. Slack Node
        slack_node = APICapabilityNode(
            node_id="slack.notification",
            provider="Slack",
            entity_type="Notification",
            input_types=["file_link", "message_text"],
            output_types=["message_status"],
            operations=["slack.chat.postMessage"],
        )
        self.add_node(slack_node)

        # Transitions
        self.add_transition("gmail.email", "drive.storage", "drive.files.create")
        self.add_transition("drive.storage", "slack.notification", "slack.chat.postMessage")

    def add_node(self, node: APICapabilityNode) -> None:
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []

    def add_transition(self, source_node_id: str, target_node_id: str, operation_id: str) -> None:
        if source_node_id not in self.adjacency:
            self.adjacency[source_node_id] = []
        self.adjacency[source_node_id].append({"target": target_node_id, "operation_id": operation_id})

    def find_path(self, source_entity: str, target_entity: str) -> List[Dict[str, Any]]:
        """Breadth-First Search (BFS) to find workflow transition paths between entities."""
        start_nodes = [nid for nid, node in self.nodes.items() if source_entity.lower() in node.entity_type.lower()]
        target_nodes = [nid for nid, node in self.nodes.items() if target_entity.lower() in node.entity_type.lower()]

        if not start_nodes or not target_nodes:
            return []

        paths = []
        for start in start_nodes:
            queue = [[start]]
            visited = set()

            while queue:
                path = queue.pop(0)
                node = path[-1]

                if node in target_nodes:
                    paths.append(path)
                    break

                if node not in visited:
                    visited.add(node)
                    for neighbor in self.adjacency.get(node, []):
                        new_path = list(path)
                        new_path.append(neighbor["target"])
                        queue.append(new_path)

        res = []
        for p in paths:
            res.append({"nodes": p, "length": len(p)})
        return res
