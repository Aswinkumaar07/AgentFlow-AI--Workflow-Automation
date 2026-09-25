import pytest
import json
from app.agents.api_discovery import dynamic_api_discovery_engine, DynamicDiscoveryResult
from app.agents.connector_ai import connector_selector, operation_ranker


def test_dynamic_api_discovery_openapi():
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Stripe Payments API", "version": "v1"},
        "paths": {
            "/v1/charges": {
                "post": {
                    "summary": "Create a new charge",
                    "operationId": "stripe.charges.create",
                    "parameters": [{"name": "amount", "required": True}, {"name": "currency", "required": True}],
                }
            },
            "/v1/customers": {
                "get": {
                    "summary": "List customers",
                    "operationId": "stripe.customers.list",
                    "parameters": [],
                }
            },
        },
    }

    res = dynamic_api_discovery_engine.discover_and_register_api(openapi_spec)
    assert isinstance(res, DynamicDiscoveryResult)
    assert res.success is True
    assert res.provider == "Stripe Payments API"
    assert res.endpoints_indexed == 2

    # Verify live registration in ConnectorSelector
    candidates = connector_selector.select_connectors("Stripe Payments API", top_k=5)
    providers = [c.provider for c in candidates]
    assert "Stripe Payments API" in providers

    # Verify live registration in OperationRanker
    ranked = operation_ranker.rank_operations("create charge", target_provider="Stripe Payments API", top_k=1)
    assert len(ranked) == 1
    assert ranked[0].operation == "stripe.charges.create"
    assert "amount" in ranked[0].parameters


def test_dynamic_api_discovery_postman():
    postman_spec = {
        "info": {"name": "Hubspot CRM API"},
        "item": [
            {
                "name": "Get Contacts",
                "request": {
                    "method": "GET",
                    "url": {"raw": "https://api.hubapi.com/crm/v3/objects/contacts"},
                },
            }
        ],
    }

    res = dynamic_api_discovery_engine.discover_and_register_api(postman_spec)
    assert res.success is True
    assert res.provider == "Hubspot CRM API"
    assert res.endpoints_indexed == 1
