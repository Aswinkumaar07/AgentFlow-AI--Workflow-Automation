import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.workflow_service import resolve_canonical_workflow_id


@pytest.mark.asyncio
async def test_uuid_and_string_id_version_resolution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Existing string ID lookups work directly
        resp_string = await client.get("/api/v1/workflows/wf_studio_1/versions")
        assert resp_string.status_code == 200
        data_string = resp_string.json().get("data", [])
        assert len(data_string) > 0

        # 2. Database UUID resolution returns identical version history
        resp_uuid = await client.get("/api/v1/workflows/3cb3623e-5aca-50cd-8db4-ac19342cd48f/versions")
        assert resp_uuid.status_code == 200
        data_uuid = resp_uuid.json().get("data", [])
        assert len(data_uuid) == len(data_string)
        assert [v["version_id"] for v in data_uuid] == [v["version_id"] for v in data_string]

        # 3. Generated workflow 1: wf_gen_7827ce74 (Test 1: Gmail)
        resp_gen1_str = await client.get("/api/v1/workflows/wf_gen_7827ce74/versions")
        assert resp_gen1_str.status_code == 200
        data_gen1_str = resp_gen1_str.json().get("data", [])
        assert len(data_gen1_str) == 1
        assert data_gen1_str[0]["name"] == "Test 1: Gmail"

        resp_gen1_uuid = await client.get("/api/v1/workflows/8189852c-d1be-5842-8282-b1ea4def5785/versions")
        assert resp_gen1_uuid.status_code == 200
        data_gen1_uuid = resp_gen1_uuid.json().get("data", [])
        assert len(data_gen1_uuid) == 1
        assert data_gen1_uuid[0]["version_id"] == data_gen1_str[0]["version_id"]
        assert data_gen1_uuid[0]["name"] == "Test 1: Gmail"

        # 4. Generated workflow 2: wf_gen_98e360d2 (Test 2: Slack only)
        resp_gen2_str = await client.get("/api/v1/workflows/wf_gen_98e360d2/versions")
        assert resp_gen2_str.status_code == 200
        data_gen2_str = resp_gen2_str.json().get("data", [])
        assert len(data_gen2_str) == 1

        resp_gen2_uuid = await client.get("/api/v1/workflows/115f7483-f24b-57ed-a25b-3d5bb5b41471/versions")
        assert resp_gen2_uuid.status_code == 200
        data_gen2_uuid = resp_gen2_uuid.json().get("data", [])
        assert len(data_gen2_uuid) == 1
        assert data_gen2_uuid[0]["version_id"] == data_gen2_str[0]["version_id"]

        # 5. Distinctness: generated workflows are NOT merged with wf_studio_1
        assert data_gen1_uuid[0]["workflow_id"] == "wf_gen_7827ce74"
        assert data_gen2_uuid[0]["workflow_id"] == "wf_gen_98e360d2"
        assert data_gen1_uuid[0]["workflow_id"] != data_gen2_uuid[0]["workflow_id"]
        assert data_uuid[0]["workflow_id"] == "wf_studio_1"

        # 6. Unknown IDs return appropriate empty result
        resp_unknown_uuid = await client.get("/api/v1/workflows/00000000-0000-0000-0000-000000000000/versions")
        assert resp_unknown_uuid.status_code == 200
        assert resp_unknown_uuid.json().get("data") == []

        resp_unknown_str = await client.get("/api/v1/workflows/wf_nonexistent_xyz/versions")
        assert resp_unknown_str.status_code == 200
        assert resp_unknown_str.json().get("data") == []


@pytest.mark.asyncio
async def test_resolve_canonical_workflow_id_unit():
    # UUIDs mapping to existing workflows
    assert await resolve_canonical_workflow_id("3cb3623e-5aca-50cd-8db4-ac19342cd48f") == "wf_studio_1"
    assert await resolve_canonical_workflow_id("8189852c-d1be-5842-8282-b1ea4def5785") == "wf_gen_7827ce74"
    assert await resolve_canonical_workflow_id("115f7483-f24b-57ed-a25b-3d5bb5b41471") == "wf_gen_98e360d2"

    # String identifiers passed as-is
    assert await resolve_canonical_workflow_id("wf_studio_1") == "wf_studio_1"
    assert await resolve_canonical_workflow_id("wf_gen_7827ce74") == "wf_gen_7827ce74"
    assert await resolve_canonical_workflow_id("custom_wf_123") == "custom_wf_123"

    # Unknown UUID returns the input UUID safely
    assert await resolve_canonical_workflow_id("00000000-0000-0000-0000-000000000000") == "00000000-0000-0000-0000-000000000000"
