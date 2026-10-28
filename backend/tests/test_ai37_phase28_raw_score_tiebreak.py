import pytest
import asyncio
from app.agents.connector_ai.operation_ranker import operation_ranker
from app.agents.api_discovery.fetcher import spec_fetcher
from app.agents.api_discovery.dynamic_discovery import dynamic_api_discovery_engine


def test_01_higher_raw_score_breaks_confidence_tie():
    orig_ops = list(operation_ranker.OPERATION_CATALOG)
    operation_ranker.OPERATION_CATALOG = [
        {
            "provider": "CustomAPI",
            "operation": "candidateB",
            "summary": "find pet by status",
            "parameters": {},
            "authentication": "APIKey",
            "keywords": ["get", "pets", "pet", "find", "status"],
        },
        {
            "provider": "CustomAPI",
            "operation": "candidateA",
            "summary": "get pet by id",
            "parameters": {},
            "authentication": "APIKey",
            "keywords": ["get", "pet", "by", "id"],
        },
    ]

    try:
        # For query "get pet by id":
        # candidateA gets modifier score (+0.15 for 'id') -> raw_score 1.30, confidence 0.99
        # candidateB gets token matches ('get', 'pets', 'pet') -> raw_score 1.15, confidence 0.99
        results = operation_ranker.rank_operations("get pet by id", target_provider="CustomAPI", top_k=2)
        assert len(results) == 2
        assert results[0].operation == "candidateA"
        assert results[1].operation == "candidateB"
        assert results[0].confidence == 0.99
        assert results[1].confidence == 0.99
    finally:
        operation_ranker.OPERATION_CATALOG = orig_ops


def test_02_petstore_get_pet_by_id_ranks_getPetById_above_findPetsByStatus():
    orig_ops = list(operation_ranker.OPERATION_CATALOG)

    petstore_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Petstore API", "version": "1.0"},
        "paths": {
            "/pet/findByStatus": {
                "get": {
                    "summary": "Finds Pets by status",
                    "description": "Finds Pets by status",
                    "operationId": "findPetsByStatus",
                    "responses": {"200": {"description": "successful operation"}}
                }
            },
            "/pet/{petId}": {
                "get": {
                    "summary": "Find pet by ID",
                    "description": "get pet details",
                    "operationId": "getPetById",
                    "responses": {"200": {"description": "successful operation"}}
                }
            }
        }
    }

    try:
        res = dynamic_api_discovery_engine.discover_and_register_api(petstore_spec)
        assert res.success is True

        ops = operation_ranker.rank_operations("get pet by id", target_provider="Petstore API", top_k=2)
        assert len(ops) >= 2
        assert ops[0].operation == "getPetById"
        assert ops[1].operation == "findPetsByStatus"
        assert ops[0].confidence == 0.99
        assert ops[1].confidence == 0.99
    finally:
        operation_ranker.OPERATION_CATALOG = orig_ops


def test_03_primary_confidence_ordering_remains_unchanged():
    orig_ops = list(operation_ranker.OPERATION_CATALOG)
    operation_ranker.OPERATION_CATALOG = [
        {
            "provider": "CustomAPI",
            "operation": "highConfidenceLowRaw",
            "summary": "get user info",
            "parameters": {},
            "authentication": "APIKey",
            "keywords": ["get", "user", "info"],
        },
        {
            "provider": "CustomAPI",
            "operation": "lowConfidenceHighRaw",
            "summary": "unmatched resource",
            "parameters": {},
            "authentication": "APIKey",
            "keywords": ["user"],
        },
    ]

    try:
        # Query matching highConfidenceLowRaw well, lowConfidenceHighRaw poorly
        results = operation_ranker.rank_operations("get user info", target_provider="CustomAPI", top_k=2)
        assert len(results) == 2
        assert results[0].operation == "highConfidenceLowRaw"
        assert results[0].confidence > results[1].confidence
    finally:
        operation_ranker.OPERATION_CATALOG = orig_ops


def test_04_exact_raw_score_tie_preserves_catalog_order():
    orig_ops = list(operation_ranker.OPERATION_CATALOG)
    operation_ranker.OPERATION_CATALOG = [
        {
            "provider": "CustomAPI",
            "operation": "firstOp",
            "summary": "get pet info",
            "parameters": {},
            "authentication": "APIKey",
            "keywords": ["get", "pet"],
        },
        {
            "provider": "CustomAPI",
            "operation": "secondOp",
            "summary": "get pet info",
            "parameters": {},
            "authentication": "APIKey",
            "keywords": ["get", "pet"],
        },
    ]

    try:
        results = operation_ranker.rank_operations("get pet info", target_provider="CustomAPI", top_k=2)
        assert len(results) == 2
        assert results[0].operation == "firstOp"
        assert results[1].operation == "secondOp"
        assert results[0].confidence == results[1].confidence
    finally:
        operation_ranker.OPERATION_CATALOG = orig_ops


def test_05_confidence_values_remain_unchanged():
    results = operation_ranker.rank_operations("send email", top_k=1)
    assert len(results) == 1
    assert results[0].confidence <= 0.99
    assert isinstance(results[0].confidence, float)
