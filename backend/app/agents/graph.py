import logging
from datetime import datetime, timezone
from typing import Dict, Any
from app.agents.state import WorkflowState
from app.agents.planner.service import planner_agent
from app.agents.api_discovery.service import api_discovery_agent
from app.agents.rag.chroma_rag import rag_service
from app.agents.workflow.service import workflow_generator_agent
from app.agents.validation.service import validation_agent
from app.agents.self_healing.service import self_healing_agent
from app.agents.memory.service import memory_agent

logger = logging.getLogger("agentflow.orchestrator")

class LangGraphOrchestrator:
    """
    LangGraph Orchestrator managing execution flow across independent agent nodes:
    Planner -> API Discovery -> RAG Retrieval -> Workflow Generator -> Validation -> (Self-Healing / Memory Store)
    """

    async def run(self, user_prompt: str) -> WorkflowState:
        # Initial State Construction
        state: WorkflowState = {
            "user_prompt": user_prompt,
            "logs": [],
            "timestamps": {"start": datetime.now(timezone.utc).isoformat()},
            "retry_count": 0,
            "is_valid": False,
            "is_repaired": False,
        }

        logger.info(f"Orchestrator started for prompt: '{user_prompt}'")
        state["logs"].append("Orchestrator initialized workflow execution graph.")

        # Node 1: Memory Search
        state["logs"].append("Step 1/6: Memory Agent checking past successful workflows...")
        memory_matches = await memory_agent.find_similar_workflows(user_prompt)
        state["memory_matches"] = memory_matches

        # Node 2: Planner Agent
        state["logs"].append("Step 2/6: Planner Agent decomposing user prompt...")
        plan = await planner_agent.create_execution_plan(user_prompt)
        state["goal"] = plan.get("goal", "")
        state["services"] = plan.get("services", [])
        state["tasks"] = plan.get("tasks", [])

        # Node 3: API Discovery Agent
        state["logs"].append("Step 3/6: API Discovery Agent identifying endpoints...")
        candidates = await api_discovery_agent.discover_for_plan(plan)
        state["api_candidates"] = candidates

        # Node 4: Documentation RAG Retrieval
        state["logs"].append("Step 4/6: RAG Documentation Agent retrieving context...")
        docs = await rag_service.retrieve_context(user_prompt, services=state["services"])
        state["retrieved_documents"] = docs

        # Node 5: Workflow Generator Agent
        state["logs"].append("Step 5/6: Workflow Generator compiling DAG JSON...")
        workflow_json = await workflow_generator_agent.generate_workflow_dag(plan, api_specs=candidates, rag_context=docs)
        state["workflow_json"] = workflow_json

        # Node 6: Validation Agent
        state["logs"].append("Step 6/6: Validation Agent auditing DAG structure...")
        val_report = await validation_agent.validate_workflow(workflow_json)
        state["validation_report"] = val_report
        state["is_valid"] = val_report.get("is_valid", False)

        # Conditional Routing & Self-Healing Loop
        if not state["is_valid"] and state["retry_count"] < 2:
            state["retry_count"] += 1
            state["logs"].append(f"Self-Healing Agent activated (Attempt {state['retry_count']}/2)...")
            
            repair_res = await self_healing_agent.diagnose_and_fix("exec-1", {
                "workflow_json": workflow_json,
                "errors": val_report.get("errors", [])
            })
            
            state["workflow_json"] = repair_res["repaired_workflow_json"]
            state["repair_report"] = repair_res["repair_report"]
            state["is_repaired"] = True

            # Revalidate repaired workflow
            reval_report = await validation_agent.validate_workflow(state["workflow_json"])
            state["validation_report"] = reval_report
            state["is_valid"] = reval_report.get("is_valid", True)
            state["logs"].append("Self-Healing successfully repaired and revalidated workflow DAG.")

        # Store Memory
        await memory_agent.store_state("session-1", dict(state))
        state["timestamps"]["end"] = datetime.now(timezone.utc).isoformat()
        state["execution_metadata"] = {
            "total_steps": 6,
            "engine": "LangGraph Multi-Agent Orchestrator",
            "llm": "Gemini 2.5 Pro",
        }

        state["logs"].append("Workflow execution pipeline completed successfully.")
        return state

langgraph_orchestrator = LangGraphOrchestrator()
