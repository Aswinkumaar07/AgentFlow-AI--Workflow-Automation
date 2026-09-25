import pytest
from app.connectors.provider_operation_registry import provider_operation_registry, ProviderOperationRegistry
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_provider_operation_registry_gmail_operations():
    # 1. Query: "What operations does Gmail support?"
    gmail_ops = provider_operation_registry.get_provider_operations("Gmail")
    assert len(gmail_ops) >= 5, f"Expected at least 5 Gmail operations, got {len(gmail_ops)}"

    op_ids = [op.id for op in gmail_ops]
    expected_ids = [
        "gmail.messages.send",
        "gmail.messages.list",
        "gmail.messages.get",
        "gmail.messages.search",
        "gmail.messages.reply",
        "gmail.messages.delete",
    ]
    for exp_id in expected_ids:
        assert exp_id in op_ids, f"Expected operation '{exp_id}' in Gmail registry operations"


def test_provider_operation_registry_github_operations():
    # 2. Query: "What operations does GitHub support?"
    github_ops = provider_operation_registry.get_provider_operations("GitHub")
    assert len(github_ops) >= 2, f"Expected at least 2 GitHub operations, got {len(github_ops)}"

    op_ids = [op.id for op in github_ops]
    assert any("issues.create" in op_id for op_id in op_ids) or any("issue" in op_id for op_id in op_ids)


def test_provider_operation_registry_metadata_lookup():
    # 3. Lookup specific operation metadata
    meta = provider_operation_registry.get_operation_metadata("gmail.messages.send")
    assert meta is not None
    assert meta.id == "gmail.messages.send"
    assert meta.display_name == "Send Email"
    assert any(p.name == "to" for p in meta.required_parameters)
    assert any(p.name == "subject" for p in meta.required_parameters)
    assert any(p.name == "body" for p in meta.required_parameters)


def test_provider_operation_registry_search_by_intent():
    # 4. Search operations by intent string
    search_results = provider_operation_registry.search_operations_by_intent("reply")
    assert len(search_results) >= 1
    assert any("reply" in op.id for op in search_results)

    slack_results = provider_operation_registry.search_operations_by_intent("slack")
    assert len(slack_results) >= 1


def test_provider_operation_registry_list_all_providers():
    # 5. List all registered providers
    providers = provider_operation_registry.list_all_providers()
    assert "gmail" in providers or "Gmail" in providers or any(p.lower() == "gmail" for p in providers)
    assert len(providers) >= 5


def test_planner_dynamic_discovery_query():
    # 6. Planner asks registry: "What operations does Gmail support?"
    planner_ops = intelligent_planner_v4.get_supported_operations("Gmail")
    assert "gmail.messages.send" in planner_ops
    assert "gmail.messages.list" in planner_ops
    assert "gmail.messages.reply" in planner_ops
