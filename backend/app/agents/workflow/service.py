from typing import Any, Dict
from app.agents.llm.enums import AgentType
from app.agents.llm.manager import llm_manager
from app.agents.llm.prompts import PromptBuilder
from app.agents.workflow.interface import BaseWorkflowGeneratorService


class WorkflowGeneratorAgent(BaseWorkflowGeneratorService):
    """Workflow Generator Agent Node for compiling plans & RAG context into DAG JSON."""

    async def generate_workflow_dag(
        self, plan: Dict[str, Any], api_specs: Any = None, rag_context: Any = None
    ) -> Dict[str, Any]:
        # If planner v2 produced structured nodes and edges, compile into DAG
        if plan and "nodes" in plan and plan["nodes"]:
            raw_nodes = plan["nodes"]
            raw_edges = plan.get("edges", [])

            react_flow_nodes = []
            for idx, n in enumerate(raw_nodes):
                op_id = n.get("operation_id") or n.get("operation", "")
                params = dict(n.get("parameters") or {})
                if op_id in ["gmail.messages.search", "gmail.messages.list"]:
                    q_val = str(params.get("q") or "").strip()
                    goal = plan.get("goal") or plan.get("user_prompt") or ""
                    noise_words = ["find email", "find emails", "search email", "search emails", "search for emails", "search my gmail", "search my email", "show me emails", "show emails", "look for emails", "get emails", "find unread emails"]
                    if not q_val or q_val == goal.strip() or any(w in q_val.lower() for w in noise_words):
                        from app.agents.planner.gmail_search_query_builder import build_gmail_search_query
                        params["q"] = build_gmail_search_query(goal, plan.get("entities"))
                    import logging
                    logger = logging.getLogger("agentflow.agents.workflow")
                    logger.info(f"[AI-17.1][FRONTEND_DAG_QUERY] step={n.get('id')} op={op_id} q='{params.get('q')}'")

                react_flow_nodes.append({
                    "id": n.get("id", f"step_{idx+1}"),
                    "type": "custom",
                    "position": {"x": 250, "y": 100 + idx * 120},
                    "data": {
                        "label": n.get("label", n.get("id")),
                        "provider": n.get("provider", "Generic"),
                        "operation_id": op_id,
                        "parameters": params,
                        "step_id": n.get("id", f"step_{idx+1}"),
                    },
                    "parameters": params,
                    "provider": n.get("provider", "Generic"),
                    "operation": op_id,
                })

            react_flow_edges = []
            for e in raw_edges:
                edge_obj = {
                    "id": e.get("id", f"e_{e.get('source')}_{e.get('target')}"),
                    "source": e.get("source"),
                    "target": e.get("target"),
                    "animated": True,
                }
                if "sourceHandle" in e:
                    edge_obj["sourceHandle"] = e["sourceHandle"]
                react_flow_edges.append(edge_obj)

            return {
                "title": plan.get("title", "AI Generated Workflow"),
                "description": plan.get("description", ""),
                "intent": plan.get("intent", ""),
                "trigger": plan.get("trigger", {}),
                "nodes": react_flow_nodes,
                "edges": react_flow_edges,
                "missing_inputs": plan.get("missing_inputs", []),
                "warnings": plan.get("warnings", []),
            }

        docs = rag_context if isinstance(rag_context, list) else []
        prompt = PromptBuilder.workflow_prompt(plan=plan, docs=docs)
        provider = llm_manager.provider_for(AgentType.WORKFLOW)
        return await provider.generate_json(prompt)

    async def generate_python_sdk(self, dag: Dict[str, Any]) -> str:
        return (
            f"# AgentFlow AI Python SDK Code\n"
            f"# Generated for DAG: {dag.get('title', 'Workflow')}\n\n"
            f"from agentflow import Client\nclient = Client()\nresult = client.execute_dag({dag})"
        )


workflow_generator_agent = WorkflowGeneratorAgent()
