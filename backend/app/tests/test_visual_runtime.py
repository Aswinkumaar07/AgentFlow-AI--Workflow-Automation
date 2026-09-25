import pytest
from app.agents.visual_runtime import visual_runtime_engine, visual_runtime_service, ExecutionTimelineSnapshot


def test_visual_runtime_color_coding_and_animation():
    exec_id = "exec_demo_100"
    nodes = [
        {"id": "step_1", "label": "Read Sheets", "provider": "Google Sheets"},
        {"id": "step_2", "label": "Loop Rows", "provider": "Loop"},
        {"id": "step_3", "label": "Send Email", "provider": "Gmail"},
    ]

    # Initialize execution: Pending status for all nodes (Blue hex #3B82F6)
    snap = visual_runtime_service.start_execution_visuals(exec_id, nodes)
    assert len(snap.steps) == 3
    assert snap.steps[0].status == "Pending"
    assert snap.steps[0].status_color == "#3B82F6"

    # Step 1 -> Running (Yellow #EAB308)
    snap1 = visual_runtime_service.record_node_event(exec_id, "step_1", "Running")
    assert snap1.steps[0].status == "Running"
    assert snap1.steps[0].status_color == "#EAB308"

    # Step 1 -> Success (Green #22C55E) with latency
    snap2 = visual_runtime_service.record_node_event(
        exec_id, "step_1", "Success", latency_ms=180, output_response={"count": 12}
    )
    assert snap2.steps[0].status == "Success"
    assert snap2.steps[0].status_color == "#22C55E"
    assert snap2.steps[0].latency_ms == 180
    assert snap2.steps[0].output_response.get("count") == 12

    # Step 2 -> Failed (Red #EF4444)
    snap3 = visual_runtime_service.record_node_event(
        exec_id, "step_2", "Failed", retries=2, log_message="Connection timeout"
    )
    assert snap3.steps[1].status == "Failed"
    assert snap3.steps[1].status_color == "#EF4444"
    assert snap3.steps[1].retries == 2
    assert "Connection timeout" in snap3.steps[1].logs

    # Step 3 -> Waiting (Orange #F97316)
    snap4 = visual_runtime_service.record_node_event(exec_id, "step_3", "Waiting")
    assert snap4.steps[2].status == "Waiting"
    assert snap4.steps[2].status_color == "#F97316"
