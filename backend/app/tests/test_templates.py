import pytest
from app.templates.engine import TemplateEngine, template_engine


@pytest.mark.asyncio
async def test_get_templates():
    templates = template_engine.get_templates()
    assert len(templates) >= 4
    titles = [t.title for t in templates]
    assert "Gmail Invoice to Drive & Slack" in titles


@pytest.mark.asyncio
async def test_get_template_by_id():
    tpl = template_engine.get_template_by_id("tpl_gmail_drive_slack")
    assert tpl is not None
    assert tpl.category == "Finance & Invoicing"
    assert "Gmail" in tpl.connectors


@pytest.mark.asyncio
async def test_clone_template():
    cloned = template_engine.clone_template("tpl_gmail_drive_slack", "user_test_clone")
    assert "wf_cloned_" in cloned["workflow_id"]
    assert cloned["tenant_id"] == "user_test_clone"
    assert len(cloned["steps"]) == 3
