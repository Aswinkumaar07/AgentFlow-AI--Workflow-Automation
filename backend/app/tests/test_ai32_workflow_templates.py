import pytest
import asyncio
from app.templates.engine import template_engine, TemplateEngine
from app.agents.validator.workflow_validator import WorkflowValidator
from app.versions.manager import workflow_version_manager
from app.runtime.workflow_executor import workflow_runtime_executor_v3

@pytest.mark.asyncio
async def test_template_registry_loads():
    templates = template_engine.get_templates()
    assert len(templates) >= 6

@pytest.mark.asyncio
async def test_template_ids_unique():
    templates = template_engine.get_templates()
    ids = [t.id for t in templates]
    assert len(ids) == len(set(ids))

@pytest.mark.asyncio
async def test_template_metadata_completeness():
    templates = template_engine.get_templates()
    for t in templates:
        assert t.id
        assert t.title
        assert t.description
        assert t.category
        assert isinstance(t.connectors, list)
        assert isinstance(t.required_providers, list)
        assert t.workflow_spec
        assert isinstance(t.configurable_parameters, list)

@pytest.mark.asyncio
async def test_template_lookup_by_id():
    tpl = template_engine.get_template_by_id('tpl_email_summarizer')
    assert tpl is not None
    assert tpl.title == 'Email Summary'

@pytest.mark.asyncio
async def test_category_filtering():
    email_tpls = template_engine.get_templates(category='Email')
    assert len(email_tpls) > 0
    for t in email_tpls:
        assert t.category.lower() == 'email'

@pytest.mark.asyncio
async def test_search_functionality():
    results = template_engine.get_templates(search='Slack')
    assert len(results) > 0
    for t in results:
        assert 'slack' in t.title.lower() or 'slack' in t.description.lower() or any('slack' in c.lower() for c in t.connectors)

@pytest.mark.asyncio
async def test_invalid_template_id_fails():
    with pytest.raises(KeyError):
        await template_engine.instantiate_template('non_existent_template_id')

@pytest.mark.asyncio
async def test_invalid_parameter_fails():
    with pytest.raises(ValueError):
        await template_engine.instantiate_template('tpl_email_summarizer', {'max_emails': 'not_a_number'})

@pytest.mark.asyncio
async def test_valid_instantiation_produces_dag():
    res = await template_engine.instantiate_template('tpl_email_summarizer', {
        'email_query': 'subject:urgent',
        'max_emails': 10
    })
    assert res['workflow_id'].startswith('wf_tpl_')
    assert len(res['nodes']) == 2
    assert len(res['edges']) == 1

@pytest.mark.asyncio
async def test_generated_dag_passes_validator():
    res = await template_engine.instantiate_template('tpl_email_slack_summary', {
        'slack_channel': '#alerts'
    })
    validator = WorkflowValidator()
    val_res = validator.validate_workflow(res['workflow_json'])
    assert val_res.is_valid is True

@pytest.mark.asyncio
async def test_correct_node_and_edge_counts():
    res = await template_engine.instantiate_template('tpl_scheduled_slack_report', {
        'slack_channel': '#all-agentflow-ai'
    })
    assert len(res['nodes']) == 4
    assert len(res['edges']) == 3

@pytest.mark.asyncio
async def test_gmail_supported_operations():
    res = await template_engine.instantiate_template('tpl_email_summarizer')
    gmail_nodes = [n for n in res['nodes'] if n['provider'] == 'gmail']
    assert len(gmail_nodes) > 0
    for n in gmail_nodes:
        assert n['operation'].startswith('gmail.')

@pytest.mark.asyncio
async def test_slack_supported_operations():
    res = await template_engine.instantiate_template('tpl_email_slack_summary', {
        'slack_channel': '#all-agentflow-ai'
    })
    slack_nodes = [n for n in res['nodes'] if n['provider'] == 'slack']
    assert len(slack_nodes) > 0
    for n in slack_nodes:
        assert n['operation'].startswith('slack.')

@pytest.mark.asyncio
async def test_ai_provider_usage():
    res = await template_engine.instantiate_template('tpl_email_summarizer')
    ai_nodes = [n for n in res['nodes'] if n['provider'] == 'ai']
    assert len(ai_nodes) > 0

@pytest.mark.asyncio
async def test_version_snapshot_creation():
    res = await template_engine.instantiate_template('tpl_invoice_email_processing', {
        'slack_channel': '#all-agentflow-ai'
    })
    wf_id = res['workflow_id']
    history = await workflow_version_manager.get_version_history(wf_id)
    assert len(history) >= 1
    assert history[0].version_number == 1
    assert history[0].node_count == 3

@pytest.mark.asyncio
async def test_version_snapshot_contains_nodes():
    res = await template_engine.instantiate_template('tpl_daily_email_digest')
    wf_id = res['workflow_id']
    snapshot = await workflow_version_manager.get_version_by_id(wf_id, res['version_id'])
    assert snapshot is not None
    assert len(snapshot.nodes) == 3

@pytest.mark.asyncio
async def test_instantiate_does_not_auto_execute():
    res = await template_engine.instantiate_template('tpl_email_summarizer')
    assert res['workflow_id'] is not None
    # Verify no execution history record created automatically
    from app.runtime.execution_history import execution_history_store
    history = await execution_history_store.list_workflow_executions(res['workflow_id'])
    assert len(history) == 0

@pytest.mark.asyncio
async def test_execution_engine_compatibility():
    res = await template_engine.instantiate_template('tpl_email_summarizer')
    wf_json = res['workflow_json']
    # Execution runtime dry invocation
    exec_result = await workflow_runtime_executor_v3.execute_workflow(wf_json, initial_context={})
    assert exec_result.execution_id is not None
    assert exec_result.status is not None

# --- Regression Tests A through F for Slack Channel Defaults ---

@pytest.mark.asyncio
async def test_slack_channel_explicit_target_channel():
    """Test A: Instantiating tpl_email_slack_summary with #all-agentflow-ai produces channel=#all-agentflow-ai."""
    res = await template_engine.instantiate_template('tpl_email_slack_summary', {
        'slack_channel': '#all-agentflow-ai'
    })
    slack_nodes = [n for n in res['nodes'] if n.get('provider') == 'slack']
    assert len(slack_nodes) > 0
    assert slack_nodes[0]['parameters']['channel'] == '#all-agentflow-ai'

@pytest.mark.asyncio
async def test_slack_channel_custom_channel():
    """Test B: Instantiating tpl_email_slack_summary with #custom-alerts preserves that custom value."""
    res = await template_engine.instantiate_template('tpl_email_slack_summary', {
        'slack_channel': '#custom-alerts'
    })
    slack_nodes = [n for n in res['nodes'] if n.get('provider') == 'slack']
    assert len(slack_nodes) > 0
    assert slack_nodes[0]['parameters']['channel'] == '#custom-alerts'

@pytest.mark.asyncio
async def test_slack_channel_missing_raises_valueerror():
    """Test C: Instantiating tpl_email_slack_summary without slack_channel raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        await template_engine.instantiate_template('tpl_email_slack_summary', {})
    assert "slack_channel" in str(excinfo.value) or "Required parameter" in str(excinfo.value)

@pytest.mark.asyncio
async def test_slack_channel_no_implicit_general_fallback():
    """Test D: Generated DAG never contains #general unless explicitly passed."""
    res = await template_engine.instantiate_template('tpl_email_slack_summary', {
        'slack_channel': '#all-agentflow-ai'
    })
    for node in res['nodes']:
        if node.get('provider') == 'slack':
            assert node['parameters']['channel'] != '#general'
            assert node['parameters']['channel'] == '#all-agentflow-ai'

@pytest.mark.asyncio
async def test_slack_channel_other_templates_require_and_preserve():
    """Test E: tpl_invoice_email_processing and tpl_scheduled_slack_report preserve explicit slack_channel."""
    res_inv = await template_engine.instantiate_template('tpl_invoice_email_processing', {
        'slack_channel': '#all-agentflow-ai'
    })
    slack_nodes_inv = [n for n in res_inv['nodes'] if n.get('provider') == 'slack']
    assert len(slack_nodes_inv) > 0
    assert slack_nodes_inv[0]['parameters']['channel'] == '#all-agentflow-ai'

    res_sched = await template_engine.instantiate_template('tpl_scheduled_slack_report', {
        'slack_channel': '#all-agentflow-ai'
    })
    slack_nodes_sched = [n for n in res_sched['nodes'] if n.get('provider') == 'slack']
    assert len(slack_nodes_sched) > 0
    assert slack_nodes_sched[0]['parameters']['channel'] == '#all-agentflow-ai'

    with pytest.raises(ValueError):
        await template_engine.instantiate_template('tpl_invoice_email_processing', {})

    with pytest.raises(ValueError):
        await template_engine.instantiate_template('tpl_scheduled_slack_report', {})

@pytest.mark.asyncio
async def test_slack_channel_parameter_metadata():
    """Test F: Parameter metadata has default=None and required=True for slack_channel."""
    for tpl_id in ['tpl_email_slack_summary', 'tpl_invoice_email_processing', 'tpl_scheduled_slack_report']:
        tpl = template_engine.get_template_by_id(tpl_id)
        assert tpl is not None
        slack_param = next((p for p in tpl.configurable_parameters if p.key == 'slack_channel'), None)
        assert slack_param is not None
        assert slack_param.default is None
        assert slack_param.required is True

