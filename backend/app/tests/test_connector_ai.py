import pytest
from app.agents.connector_ai import (
    connector_selector,
    ConnectorCandidate,
    operation_ranker,
    OperationResult,
    connector_ai_service,
)


def test_connector_selector_semantic_search():
    candidates = connector_selector.select_connectors("Send good morning email to customer", top_k=3)
    assert len(candidates) > 0
    assert candidates[0].provider == "Gmail"
    assert candidates[0].authentication == "OAuth2"
    assert candidates[0].confidence > 0.4


def test_connector_selector_slack_github():
    candidates = connector_selector.select_connectors("Notify Slack when GitHub PR opens", top_k=5)
    providers = [c.provider for c in candidates]
    assert "Slack" in providers
    assert "GitHub" in providers


def test_operation_ranker():
    ranked = operation_ranker.rank_operations("send email message", target_provider="Gmail", top_k=2)
    assert len(ranked) > 0
    assert ranked[0].provider == "Gmail"
    assert ranked[0].operation == "gmail.messages.send"
    assert "to" in ranked[0].parameters
    assert ranked[0].authentication == "OAuth2"


def test_operation_ranker_ai_summarize():
    ranked = operation_ranker.rank_operations("AI summarize text", target_provider="AI", top_k=1)
    assert len(ranked) == 1
    assert ranked[0].provider == "AI"
    assert ranked[0].operation == "ai.summarize"
    assert ranked[0].authentication == "APIKey"


def test_connector_ai_service_discovery():
    discovery = connector_ai_service.discover_connectors_and_operations("Read employees from Google Sheets and loop over rows")
    assert "candidates" in discovery
    assert "ranked_operations" in discovery
    providers = [c["provider"] for c in discovery["candidates"]]
    assert "Google Sheets" in providers or "Loop" in providers
