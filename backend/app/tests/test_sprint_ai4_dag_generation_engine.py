import pytest
from app.agents.dag_generator import enterprise_dag_generator, WorkflowGraphResult
from app.agents.task_decomposer import DecomposedTask
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_dag_generation_nodes_edges_visualization():
    tasks = [
        DecomposedTask(step=1, name="List Emails", provider="gmail", operation="gmail.messages.list", depends_on=[]),
        DecomposedTask(step=2, name="Read Details", provider="gmail", operation="gmail.messages.get", depends_on=[1]),
        DecomposedTask(step=3, name="Gemini Summary", provider="ai", operation="ai.summarize", depends_on=[2]),
    ]

    dag_result = enterprise_dag_generator.generate_dag(tasks)
    assert isinstance(dag_result, WorkflowGraphResult)
    assert len(dag_result.nodes) == 3
    assert len(dag_result.edges) == 2

    # Check node details & position coordinates
    node1 = dag_result.nodes[0]
    assert node1.id == "step_1"
    assert node1.provider == "gmail"
    assert node1.position.x == 250.0
    assert node1.position.y == 100.0
    assert node1.metadata["color"] == "#EA4335"

    node3 = dag_result.nodes[2]
    assert node3.id == "step_3"
    assert node3.provider == "ai"
    assert node3.position.y == 360.0  # 100 + 2*130

    # Check edge dependencies
    edge1 = dag_result.edges[0]
    assert edge1.source == "step_1"
    assert edge1.target == "step_2"

    edge2 = dag_result.edges[1]
    assert edge2.source == "step_2"
    assert edge2.target == "step_3"

    # Check visualization metadata
    viz = dag_result.visualization
    assert viz["layout"] == "DAG"
    assert viz["node_count"] == 3
    assert viz["edge_count"] == 2


def test_dag_generation_branching_and_triggers():
    tasks = [
        DecomposedTask(step=1, name="Schedule Trigger", provider="schedule", operation="schedule.trigger", depends_on=[]),
        DecomposedTask(step=2, name="Generate Email", provider="ai", operation="ai.email_writer", depends_on=[]),
        DecomposedTask(step=3, name="Send Gmail", provider="gmail", operation="gmail.messages.send", depends_on=[1, 2]),
    ]

    dag_result = enterprise_dag_generator.generate_dag(tasks)
    assert len(dag_result.nodes) == 3
    assert len(dag_result.edges) == 3
    assert dag_result.nodes[0].type == "trigger"

    # Check non-sequential branching edges pointing to step_3
    targets = [e.target for e in dag_result.edges]
    assert targets.count("step_3") == 2


def test_planner_v4_dag_visualization_integration():
    plan = intelligent_planner_v4.plan("Read unread emails and summarize")
    assert "visualization" in plan.workflow_graph
    viz = plan.workflow_graph["visualization"]
    assert viz["layout"] == "DAG"
    assert viz["node_count"] >= 1
