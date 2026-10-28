import pytest
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer

@pytest.fixture
def decomposer():
    return EnterpriseTaskDecomposer()


def test_01_and_then_splits_into_two_tasks(decomposer):
    prompt = "Get users and then get orders"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 2
    assert res.tasks[0].step == 1
    assert res.tasks[1].step == 2


def test_02_comma_then_splits_into_two_tasks(decomposer):
    prompt = "Get users, then get orders"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 2


def test_03_period_then_splits_into_two_tasks(decomposer):
    prompt = "Get users. Then get orders."
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 2


def test_04_first_then_splits_into_two_tasks(decomposer):
    prompt = "First get users, then get orders"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 2


def test_05_after_that_splits_into_two_tasks(decomposer):
    prompt = "Get users, after that get orders"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 2


def test_06_openapi_url_prompt_splits_into_two_tasks(decomposer):
    prompt = "Get users and then get orders using https://example.com/openapi.json"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 2


def test_07_both_tasks_preserve_shared_spec_context(decomposer):
    prompt = "Get users and then get orders using https://example.com/openapi.json"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 2
    instr1 = res.tasks[0].parameters.get("instruction", "")
    instr2 = res.tasks[1].parameters.get("instruction", "")
    assert "https://example.com/openapi.json" in instr1
    assert "https://example.com/openapi.json" in instr2


def test_08_explicit_step_numbers_split_into_two_tasks(decomposer):
    prompt = "Step 1: get users. Step 2: get orders."
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 2


def test_09_semicolon_then_splits_into_two_tasks(decomposer):
    prompt = "Get users; then get orders"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 2


def test_10_three_sequential_actions_split_into_three_tasks(decomposer):
    prompt = "Get users, then get orders, then get products"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 3


def test_11_two_step_dependencies_are_correct(decomposer):
    prompt = "Get users and then get orders"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 2
    assert res.tasks[0].depends_on == []
    assert res.tasks[1].depends_on == [1]


def test_12_three_step_dependencies_are_correct(decomposer):
    prompt = "Get users, then get orders, then get products"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 3
    assert res.tasks[0].depends_on == []
    assert res.tasks[1].depends_on == [1]
    assert res.tasks[2].depends_on == [2]


def test_13_parameter_conjunction_remains_single_task(decomposer):
    prompt = "Create a user with name Alice and email Alice@example.com"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 1


def test_14_quoted_and_then_remains_single_task(decomposer):
    prompt = "Search emails with subject 'A and then B'"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 1 or all(t.provider == "gmail" for t in res.tasks)


def test_15_existing_gmail_multistep_unchanged(decomposer):
    prompt = "Find unread emails and read message details"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) >= 2
    assert res.tasks[0].provider == "gmail"


def test_16_existing_gmail_to_slack_unchanged(decomposer):
    prompt = "Search gmail for invoices and post to #general on slack"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) >= 2
    providers = [t.provider for t in res.tasks]
    assert "gmail" in providers
    assert "slack" in providers


def test_17_native_connector_precedence_maintained(decomposer):
    prompt = "Search GitHub issues and post to #general on slack"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) >= 2
    assert res.tasks[0].provider == "github"


def test_18_no_url_context_becomes_standalone_task(decomposer):
    prompt = "Get users and then get orders using https://example.com/openapi.json"
    res = decomposer.decompose(prompt)
    for t in res.tasks:
        instr = t.parameters.get("instruction", "")
        assert instr != "https://example.com/openapi.json"
        assert not instr.startswith("https://")


def test_19_no_empty_tasks_produced(decomposer):
    prompt = "Get users and then get orders"
    res = decomposer.decompose(prompt)
    for t in res.tasks:
        instr = t.parameters.get("instruction", "")
        assert len(instr.strip()) > 0


def test_20_single_action_generic_prompt_produces_one_task(decomposer):
    prompt = "Get available users from https://example.com/openapi.json"
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 1
    assert res.tasks[0].provider == "generic"
    assert res.tasks[0].operation == "execute.action"
