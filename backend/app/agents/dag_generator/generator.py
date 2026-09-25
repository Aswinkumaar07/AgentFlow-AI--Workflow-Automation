import logging
from typing import List, Dict, Any, Optional

from app.agents.task_decomposer.models import DecomposedTask, TaskDecompositionResult
from app.agents.dag_generator.models import (
    DAGNodeModel,
    DAGEdgeModel,
    PositionModel,
    WorkflowGraphResult,
)

logger = logging.getLogger("agentflow.agents.dag_generator")


class EnterpriseDAGGenerator:
    """
    Sprint AI-4: Enterprise Dynamic DAG Generation Engine for AgentFlow AI.
    Converts task decomposition lists into executable workflow graphs with nodes, edges, branching, conditions,
    and React Flow visualization metadata.
    """

    PROVIDER_COLOR_MAP = {
        "gmail": "#EA4335",
        "google": "#4285F4",
        "drive": "#0F9D58",
        "slack": "#4A154B",
        "github": "#24292E",
        "schedule": "#FF9900",
        "ai": "#8E44AD",
        "condition": "#F39C12",
        "stripe": "#6772E5",
    }

    def generate_dag(
        self,
        tasks: List[DecomposedTask],
        trigger_info: Optional[Dict[str, Any]] = None,
        has_condition: bool = False,
    ) -> WorkflowGraphResult:
        dag_nodes: List[DAGNodeModel] = []
        dag_edges: List[DAGEdgeModel] = []

        if not tasks:
            return WorkflowGraphResult(nodes=[], edges=[], visualization={"layout": "DAG", "node_count": 0, "edge_count": 0})

        # 1. Generate Nodes with React Flow Layout Coordinates & UI Metadata
        for idx, task in enumerate(tasks):
            step_num = task.step or (idx + 1)
            node_id = f"step_{step_num}"
            provider = (task.provider or "gmail").lower()
            operation = task.operation or "gmail.messages.send"

            # Node Type Determination
            node_type = "action"
            if idx == 0 and (provider == "schedule" or trigger_info):
                node_type = "trigger"
            elif "condition" in provider or "if" in operation:
                node_type = "condition"

            # Auto Position Layout Calculation (UI Grid)
            x_pos = 250.0 + ((step_num - 1) * 40.0 if node_type == "condition" else 0.0)
            y_pos = 100.0 + ((step_num - 1) * 130.0)

            color = self.PROVIDER_COLOR_MAP.get(provider, "#2563EB")
            metadata = {
                "icon": provider,
                "color": color,
                "category": "Communication" if provider in ["gmail", "slack"] else "Automation",
                "auth_status": "active",
            }

            node = DAGNodeModel(
                id=node_id,
                step_id=node_id,
                label=task.name or f"Step {step_num}",
                type=node_type,
                provider=provider,
                operation=operation,
                parameters=task.parameters or {},
                position=PositionModel(x=x_pos, y=y_pos),
                metadata=metadata,
            )
            dag_nodes.append(node)

        # 2. Generate Edges (Dependencies & Branching)
        for idx, task in enumerate(tasks):
            current_id = f"step_{task.step or (idx + 1)}"

            if task.depends_on:
                for dep_step in task.depends_on:
                    source_id = f"step_{dep_step}"
                    edge_id = f"e{dep_step}-{task.step or (idx + 1)}"
                    dag_edges.append(DAGEdgeModel(id=edge_id, source=source_id, target=current_id))
            elif idx > 0:
                prev_id = f"step_{tasks[idx - 1].step or idx}"
                edge_id = f"e{idx}-{idx + 1}"
                dag_edges.append(DAGEdgeModel(id=edge_id, source=prev_id, target=current_id))

        # 3. Visualization Metadata Summary
        viz_metadata = {
            "layout": "DAG",
            "node_count": len(dag_nodes),
            "edge_count": len(dag_edges),
            "has_trigger": any(n.type == "trigger" for n in dag_nodes),
            "has_condition": any(n.type == "condition" for n in dag_nodes),
            "flow_direction": "vertical",
        }

        result = WorkflowGraphResult(nodes=dag_nodes, edges=dag_edges, visualization=viz_metadata)
        logger.info(f"[AI-4] Generated Workflow DAG with {len(dag_nodes)} nodes and {len(dag_edges)} edges")
        return result


enterprise_dag_generator = EnterpriseDAGGenerator()
