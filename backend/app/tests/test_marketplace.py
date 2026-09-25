import pytest
from app.agents.marketplace import marketplace_ai_service, MarketplaceTemplate


def test_marketplace_publish_recommend_personalize():
    graph = {
        "title": "Finance Invoice Processor",
        "nodes": [
            {"id": "step_1", "provider": "Stripe", "operation_id": "stripe.invoices.list"},
            {"id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.send"},
        ],
    }

    # 1. Publish workflow with AI metadata extraction
    tpl = marketplace_ai_service.publish(
        title="Finance Invoice Processor",
        description="Processes Stripe invoices and emails finance team.",
        workflow_graph=graph,
        author="FinTech Dev",
    )
    assert isinstance(tpl, MarketplaceTemplate)
    assert tpl.industry == "Finance"
    assert tpl.difficulty == "Beginner"

    # 2. Search & recommend template
    results = marketplace_ai_service.search_recommend("Finance")
    assert len(results) >= 1
    assert any(r.title == "Finance Invoice Processor" for r in results)

    # 3. Personalize template for user context
    pers = marketplace_ai_service.personalize(tpl.id, {"email": "finance@company.com", "company": "Acme Inc"})
    assert pers.get("is_personalized") is True
    assert pers["nodes"][1]["parameters"]["recipient"] == "finance@company.com"

    # 4. Fork workflow template
    forked = marketplace_ai_service.fork(tpl.id, user_id="DevUser")
    assert "Fork of" in forked.title
    assert forked.workflow_graph.get("forked_from") == tpl.id

    # 5. Rate & Comment
    rated = marketplace_ai_service.rate(tpl.id, 5.0)
    assert rated.rating_count > 12

    commented = marketplace_ai_service.comment(tpl.id, "Alice", "Awesome pipeline!")
    assert len(commented.comments) >= 1
    assert commented.comments[-1].content == "Awesome pipeline!"
