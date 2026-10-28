import pytest
import asyncio
from app.agents.api_discovery.models import EndpointMetadataModel
from app.agents.api_discovery.dynamic_discovery import _extract_meaningful_keywords, dynamic_api_discovery_engine
from app.agents.connector_ai.operation_ranker import operation_ranker, _stem


def test_01_plural_singular_deduplication():
    ep = EndpointMetadataModel(
        provider="Petstore",
        operation_id="findPetsByStatus",
        endpoint="/pet/findByStatus",
        http_method="GET",
        summary="Finds Pets by status",
    )
    keywords = _extract_meaningful_keywords(ep, "Petstore")
    assert "pet" in keywords
    assert "pets" not in keywords


def test_02_verb_inflection_deduplication():
    ep = EndpointMetadataModel(
        provider="Petstore",
        operation_id="updatePetWithForm",
        endpoint="/pet/{petId}",
        http_method="POST",
        summary="Updates a pet in the store with form data",
    )
    keywords = _extract_meaningful_keywords(ep, "Petstore")
    assert "update" in keywords
    assert "updates" not in keywords


def test_03_no_duplicate_stems_in_generated_keywords():
    ep = EndpointMetadataModel(
        provider="Petstore",
        operation_id="findPetsByStatus",
        endpoint="/pet/findByStatus",
        http_method="GET",
        summary="Finds Pets by status and category",
    )
    keywords = _extract_meaningful_keywords(ep, "Petstore")
    stems = [_stem(k) for k in keywords]
    assert len(stems) == len(set(stems))


def test_04_important_distinct_words_remain():
    ep = EndpointMetadataModel(
        provider="Petstore",
        operation_id="updatePetWithForm",
        endpoint="/pet/{petId}",
        http_method="POST",
        summary="Updates a pet in the store with form data",
    )
    keywords = _extract_meaningful_keywords(ep, "Petstore")
    stems = set(keywords)
    assert "pet" in stems
    assert "update" in stems
    assert "form" in stems
    assert "data" in stems


def test_05_petstore_findPetsByStatus_metadata():
    ep = EndpointMetadataModel(
        provider="Petstore",
        operation_id="findPetsByStatus",
        endpoint="/pet/findByStatus",
        http_method="GET",
        summary="Finds Pets by status",
    )
    keywords = _extract_meaningful_keywords(ep, "Petstore")
    assert keywords.count("pet") == 1
    assert "pets" not in keywords


def test_06_petstore_updatePetWithForm_metadata():
    ep = EndpointMetadataModel(
        provider="Petstore",
        operation_id="updatePetWithForm",
        endpoint="/pet/{petId}",
        http_method="POST",
        summary="Updates a pet in the store with form data",
    )
    keywords = _extract_meaningful_keywords(ep, "Petstore")
    assert keywords.count("update") == 1
    assert "updates" not in keywords


def test_07_operation_registration_metadata_integrity():
    petstore_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Petstore", "version": "1.0"},
        "paths": {
            "/pet/{petId}": {
                "get": {
                    "summary": "Find pet by ID",
                    "operationId": "getPetById",
                    "responses": {"200": {"description": "successful operation"}}
                }
            }
        }
    }
    orig_ops = list(operation_ranker.OPERATION_CATALOG)
    try:
        res = dynamic_api_discovery_engine.discover_and_register_api(petstore_spec)
        assert res.success is True
        cat_item = next(it for it in operation_ranker.OPERATION_CATALOG if it["operation"] == "getPetById" and it["provider"] == "Petstore")
        assert cat_item["operation"] == "getPetById"
        assert cat_item["parameters"]["url"] == "https://petstore3.swagger.io/api/v3/pet/{petId}"
        assert cat_item["authentication"] in ["APIKey", "None"]
    finally:
        operation_ranker.OPERATION_CATALOG = orig_ops


def test_08_ranking_regression_checks():
    orig_ops = list(operation_ranker.OPERATION_CATALOG)
    petstore_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Petstore API", "version": "1.0"},
        "paths": {
            "/pet": {
                "put": {
                    "summary": "Update an existing pet",
                    "operationId": "updatePet",
                    "responses": {"200": {"description": "successful operation"}}
                }
            },
            "/pet/{petId}": {
                "get": {
                    "summary": "Find pet by ID",
                    "operationId": "getPetById",
                    "responses": {"200": {"description": "successful operation"}}
                },
                "post": {
                    "summary": "Updates a pet in the store with form data",
                    "operationId": "updatePetWithForm",
                    "responses": {"200": {"description": "successful operation"}}
                }
            },
            "/pet/findByStatus": {
                "get": {
                    "summary": "Finds Pets by status",
                    "operationId": "findPetsByStatus",
                    "responses": {"200": {"description": "successful operation"}}
                }
            }
        }
    }

    try:
        dynamic_api_discovery_engine.discover_and_register_api(petstore_spec)

        # Query A: "update a pet" -> updatePet must rank above updatePetWithForm
        ops_a = operation_ranker.rank_operations("update a pet", target_provider="Petstore API", top_k=2)
        assert len(ops_a) >= 2
        assert ops_a[0].operation == "updatePet"

        # Query B: "get pet by id" -> getPetById must rank above findPetsByStatus
        ops_b = operation_ranker.rank_operations("get pet by id", target_provider="Petstore API", top_k=2)
        assert len(ops_b) >= 2
        assert ops_b[0].operation == "getPetById"
    finally:
        operation_ranker.OPERATION_CATALOG = orig_ops
