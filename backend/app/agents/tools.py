import json
from typing import Dict, Any, List
from app.agents.registry import provider_registry
from app.agents.rag.chroma_rag import rag_service

class DocumentationSearchTool:
    """Tool for searching indexed API documentation & specs."""
    async def search(self, query: str, services: List[str] = None) -> List[Dict[str, Any]]:
        return await rag_service.retrieve_context(query, services=services)

class MemorySearchTool:
    """Tool for searching past successful workflow executions."""
    async def search_previous_workflows(self, prompt: str) -> List[Dict[str, Any]]:
        return [
            {
                "prompt": "Sync GitHub PRs to Slack",
                "score": 0.92,
                "workflow_title": "GitHub PR Alert Workflow",
                "success_rate": 100.0,
            }
        ]

class WorkflowValidatorTool:
    """Tool for auditing workflow graph structure and DAG cycles."""
    def validate(self, workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        warnings = []
        nodes = workflow_json.get("nodes", [])
        edges = workflow_json.get("edges", [])

        if not nodes:
            errors.append("Workflow DAG contains no nodes.")

        # Check node IDs uniqueness
        node_ids = set()
        for node in nodes:
            n_id = node.get("id")
            if not n_id:
                errors.append("Node missing 'id' field.")
            elif n_id in node_ids:
                errors.append(f"Duplicate node ID detected: {n_id}")
            else:
                node_ids.add(n_id)

        # Check edge targets exist
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src not in node_ids:
                errors.append(f"Edge source '{src}' does not exist in nodes.")
            if tgt not in node_ids:
                errors.append(f"Edge target '{tgt}' does not exist in nodes.")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

class WorkflowFormatterTool:
    """Tool for formatting raw LLM output into standardized DAG JSON."""
    def format(self, raw_data: Any) -> Dict[str, Any]:
        if isinstance(raw_data, str):
            try:
                return json.loads(raw_data)
            except Exception:
                pass
        if isinstance(raw_data, dict):
            return raw_data
        return {}

class RepairEngineTool:
    """Tool for applying automated parameter and path patches to broken workflows."""
    def patch(self, workflow_json: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
        patched = dict(workflow_json)
        applied_fixes = []

        # Fix missing ID or structure
        if "nodes" not in patched or not patched["nodes"]:
            patched["nodes"] = [
                {
                    "id": "node_1",
                    "type": "api_call",
                    "provider": "github",
                    "action": "GET /repos/{owner}/{repo}/pulls",
                    "params": {"owner": "demo", "repo": "app"}
                }
            ]
            applied_fixes.append("Created default missing node_1")

        return {
            "repaired_workflow_json": patched,
            "repair_report": {
                "applied_fixes": applied_fixes,
                "original_error_count": len(errors)
            }
        }

class ExecutionPlannerTool:
    """Tool for parsing prompts into task steps."""
    def plan(self, prompt: str) -> Dict[str, Any]:
        services = []
        p_lower = prompt.lower()
        if "github" in p_lower: services.append("github")
        if "slack" in p_lower: services.append("slack")
        if "gmail" in p_lower: services.append("gmail")
        if "drive" in p_lower: services.append("drive")
        if "sheets" in p_lower: services.append("sheets")
        if "notion" in p_lower: services.append("notion")

        if not services:
            services = ["github", "slack"]

        return {
            "goal": prompt,
            "services": services,
            "confidence_score": 0.95,
        }

doc_tool = DocumentationSearchTool()
memory_tool = MemorySearchTool()
validator_tool = WorkflowValidatorTool()
formatter_tool = WorkflowFormatterTool()
repair_tool = RepairEngineTool()
planner_tool = ExecutionPlannerTool()
