import pytest
from app.analytics.engine import AnalyticsEngine, analytics_engine


@pytest.mark.asyncio
async def test_analytics_overview_metrics():
    overview = analytics_engine.get_overview_metrics("7d")
    assert overview["total_executions"] > 0
    assert 0.0 <= overview["success_rate_pct"] <= 100.0
    assert len(overview["execution_trend"]) > 0


@pytest.mark.asyncio
async def test_connector_health_metrics():
    health = analytics_engine.get_connector_health()
    assert len(health) >= 5
    provider_names = [h["provider"] for h in health]
    assert "Google Gmail" in provider_names
    assert "Slack Web API" in provider_names


@pytest.mark.asyncio
async def test_ai_insights():
    insights = analytics_engine.get_ai_optimization_insights()
    assert len(insights) >= 2
    types = [i["type"] for i in insights]
    assert "PARALLEL_OPPORTUNITY" in types
