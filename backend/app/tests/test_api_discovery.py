import pytest
import time
from app.agents.api_discovery import (
    APIDiscoveryAgent,
    APIEndpointModel,
    EnterpriseCache,
    EnterpriseSpecParser,
    EmbeddingGenerator,
    HybridRanker,
    CapabilityGraph,
    VectorStore,
    api_discovery_agent,
    catalog_crawler,
    embedding_manager,
    event_stream,
    governance_engine,
    learning_engine,
    tenant_manager,
)


@pytest.mark.asyncio
async def test_embedding_strategy_manager():
    provider = embedding_manager.get_active_provider("local")
    assert provider.provider_name == "local"

    vec = await embedding_manager.generate_embedding("Test email query", provider_name="local")
    assert len(vec) == 384


@pytest.mark.asyncio
async def test_workflow_learning_engine():
    learning_engine.record_execution("Gmail", "gmail.messages.list", latency_ms=80.0, success=True)
    health = learning_engine.get_health_score("Gmail")
    assert 0.0 <= health <= 1.0


@pytest.mark.asyncio
async def test_api_governance_engine():
    ep = APIEndpointModel(
        endpoint="/v1/old",
        operation_id="old.v1.op",
        provider="LegacyProvider",
        deprecation_status=True,
    )
    audit = governance_engine.audit_endpoint(ep)
    assert audit["status"] == "DEPRECATED"


@pytest.mark.asyncio
async def test_tenant_isolation_manager():
    ep = APIEndpointModel(
        endpoint="/v1/tenant_custom",
        operation_id="tenant.custom.op",
        provider="TenantPrivateAPI",
    )
    tenant_manager.register_tenant_endpoint("tenant_123", ep)
    tenant_eps = tenant_manager.get_tenant_endpoints("tenant_123")
    assert len(tenant_eps) == 1
    assert tenant_eps[0].provider == "TenantPrivateAPI"


@pytest.mark.asyncio
async def test_event_streaming_engine():
    events_received = []

    def on_event(evt):
        events_received.append(evt)

    event_stream.subscribe("DiscoveryCompleted", on_event)
    event_stream.publish("DiscoveryCompleted", {"summary": "Completed 1 query"})

    assert len(events_received) == 1
    assert events_received[0]["event_type"] == "DiscoveryCompleted"


@pytest.mark.asyncio
async def test_spec_parser_openapi():
    parser = EnterpriseSpecParser()
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Payment Gateway", "version": "v2"},
        "paths": {
            "/v2/payments": {
                "post": {
                    "summary": "Process payment transaction",
                    "operationId": "payments.create",
                    "parameters": [{"name": "amount", "required": True}],
                }
            }
        },
    }
    parsed = parser.parse_spec(openapi_spec)
    assert len(parsed) == 1
    assert parsed[0].provider == "Payment Gateway"
    assert parsed[0].operation_id == "payments.create"


@pytest.mark.asyncio
async def test_embedding_generator_and_vectorstore():
    generator = EmbeddingGenerator(dimension=384)
    store = VectorStore()

    vec1 = await generator.generate_embedding("Send email message via Gmail inbox")
    vec2 = await generator.generate_embedding("Create payment charge via Stripe")

    ep1 = APIEndpointModel(
        endpoint="/v1/messages",
        operation_id="gmail.messages.list",
        provider="Gmail",
        summary="List unread emails",
        embedding=vec1,
    )
    ep2 = APIEndpointModel(
        endpoint="/v1/charges",
        operation_id="stripe.charges.create",
        provider="Stripe",
        summary="Create charge",
        embedding=vec2,
    )

    await store.add_endpoints([ep1, ep2])

    query_vec = await generator.generate_embedding("Check email inbox message")
    results = await store.search_vectors(query_vec, top_k=2)

    assert len(results) == 2
    assert results[0].provider == "Gmail"


@pytest.mark.asyncio
async def test_hybrid_ranker():
    ranker = HybridRanker()
    ep1 = APIEndpointModel(
        endpoint="/v1/messages",
        operation_id="gmail.messages.list",
        provider="Gmail",
        summary="List Gmail messages inbox",
        confidence_score=0.90,
        popularity_score=0.98,
        health_score=1.0,
        latency_ms=80.0,
    )
    ep2 = APIEndpointModel(
        endpoint="/v1/tickets",
        operation_id="generic.tickets.create",
        provider="Generic",
        summary="Create generic ticket",
        confidence_score=0.50,
        popularity_score=0.50,
        health_score=0.80,
        latency_ms=300.0,
    )

    ranked = ranker.rank([ep1, ep2], query="Gmail invoice email", query_vector=[0.1] * 384)
    assert ranked[0].provider == "Gmail"
    assert ranked[0].confidence_score > ranked[1].confidence_score


@pytest.mark.asyncio
async def test_capability_graph():
    graph = CapabilityGraph()
    path = graph.find_path(source_entity="Email", target_entity="Notification")
    assert len(path) > 0
    assert "nodes" in path[0]


@pytest.mark.asyncio
async def test_sub_50ms_vector_search_benchmark():
    store = VectorStore()
    query_vec = [0.1] * 384

    start = time.perf_counter()
    results = await store.search_vectors(query_vec, top_k=5)
    duration_ms = (time.perf_counter() - start) * 1000.0

    assert duration_ms < 50.0, f"Vector search time was {duration_ms:.2f}ms, expected sub-50ms!"
