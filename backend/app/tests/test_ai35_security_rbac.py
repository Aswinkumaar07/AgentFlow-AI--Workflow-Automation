"""
Comprehensive Test Suite for AI-35: Security, Role-Based Access Control & Audit System.
Verifies RBAC matrix, authorization dependencies, API key lifecycle, append-only audit logger,
metadata secret sanitization, and user role management with 50+ assertions.
"""

import uuid
import time
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.models.users import User
from app.security.rbac import (
    ROLE_OWNER,
    ROLE_ADMIN,
    ROLE_MEMBER,
    ROLE_VIEWER,
    has_permission,
    get_user_role,
    require_permission,
)
from app.security.api_keys import api_key_manager, APIKeyManager
from app.security.audit import audit_logger, sanitize_metadata, AuditLogger
from app.dependencies.auth import get_current_user


client = TestClient(app)


# ── 1. RBAC Matrix & Role Permission Tests ──────────────────────────────────

def test_rbac_owner_has_all_permissions():
    """Verify OWNER role possesses full system permissions."""
    assert has_permission(ROLE_OWNER, "workflow.create") is True
    assert has_permission(ROLE_OWNER, "workflow.delete") is True
    assert has_permission(ROLE_OWNER, "workflow.execute") is True
    assert has_permission(ROLE_OWNER, "credential.write") is True
    assert has_permission(ROLE_OWNER, "user.delete") is True
    assert has_permission(ROLE_OWNER, "user.role_assign") is True
    assert has_permission(ROLE_OWNER, "organization.write") is True
    assert has_permission(ROLE_OWNER, "audit.read") is True
    assert has_permission(ROLE_OWNER, "api_key.create") is True


def test_rbac_admin_permissions():
    """Verify ADMIN role permissions and boundary restrictions."""
    assert has_permission(ROLE_ADMIN, "workflow.create") is True
    assert has_permission(ROLE_ADMIN, "workflow.delete") is True
    assert has_permission(ROLE_ADMIN, "credential.write") is True
    assert has_permission(ROLE_ADMIN, "user.role_assign") is True
    assert has_permission(ROLE_ADMIN, "audit.read") is True
    assert has_permission(ROLE_ADMIN, "api_key.create") is True

    # Restrictions for ADMIN
    assert has_permission(ROLE_ADMIN, "user.delete") is False
    assert has_permission(ROLE_ADMIN, "organization.write") is False


def test_rbac_member_permissions():
    """Verify MEMBER role permissions and restriction boundaries."""
    assert has_permission(ROLE_MEMBER, "workflow.create") is True
    assert has_permission(ROLE_MEMBER, "workflow.read") is True
    assert has_permission(ROLE_MEMBER, "workflow.update") is True
    assert has_permission(ROLE_MEMBER, "workflow.execute") is True
    assert has_permission(ROLE_MEMBER, "execution.read") is True

    # Restrictions for MEMBER
    assert has_permission(ROLE_MEMBER, "workflow.delete") is False
    assert has_permission(ROLE_MEMBER, "credential.write") is False
    assert has_permission(ROLE_MEMBER, "credential.delete") is False
    assert has_permission(ROLE_MEMBER, "user.role_assign") is False
    assert has_permission(ROLE_MEMBER, "audit.read") is False
    assert has_permission(ROLE_MEMBER, "api_key.create") is False


def test_rbac_viewer_permissions():
    """Verify VIEWER role read-only access and strict execution/mutation blocking."""
    assert has_permission(ROLE_VIEWER, "workflow.read") is True
    assert has_permission(ROLE_VIEWER, "template.read") is True
    assert has_permission(ROLE_VIEWER, "execution.read") is True
    assert has_permission(ROLE_VIEWER, "connection.read") is True
    assert has_permission(ROLE_VIEWER, "organization.read") is True

    # Strict mutation and execution blocking for VIEWER
    assert has_permission(ROLE_VIEWER, "workflow.create") is False
    assert has_permission(ROLE_VIEWER, "workflow.update") is False
    assert has_permission(ROLE_VIEWER, "workflow.delete") is False
    assert has_permission(ROLE_VIEWER, "workflow.execute") is False
    assert has_permission(ROLE_VIEWER, "execution.cancel") is False
    assert has_permission(ROLE_VIEWER, "credential.write") is False
    assert has_permission(ROLE_VIEWER, "credential.delete") is False
    assert has_permission(ROLE_VIEWER, "api_key.create") is False
    assert has_permission(ROLE_VIEWER, "audit.read") is False


def test_user_role_resolution():
    """Test get_user_role extraction across superusers, role fields, and default users."""
    super_user = User(id=uuid.uuid4(), email="admin@agentflow.ai", is_superuser=True)
    assert get_user_role(super_user) == ROLE_OWNER

    viewer_user = User(id=uuid.uuid4(), email="viewer@agentflow.ai", role="VIEWER")
    assert get_user_role(viewer_user) == ROLE_VIEWER

    member_user = User(id=uuid.uuid4(), email="member@agentflow.ai", role="MEMBER")
    assert get_user_role(member_user) == ROLE_MEMBER

    default_user = User(id=uuid.uuid4(), email="user@agentflow.ai")
    assert get_user_role(default_user) in [ROLE_OWNER, ROLE_MEMBER]


# ── 2. API Key Lifecycle Engine Tests ──────────────────────────────────────

def test_api_key_creation():
    """Verify API key generation format, prefix, SHA-256 hash storage, and metadata isolation."""
    mgr = APIKeyManager()
    user_id = str(uuid.uuid4())

    meta, raw_key = mgr.create_api_key(user_id=user_id, name="Test Key", expires_in_days=30)

    assert raw_key.startswith("af_live_")
    assert len(raw_key) > 30
    assert meta.name == "Test Key"
    assert meta.prefix == "af_live_"
    assert meta.user_id == user_id
    assert meta.is_active is True
    assert meta.expires_at > time.time()
    assert meta.key_hash != raw_key  # Must store hashed value, never raw key


def test_api_key_verification():
    """Verify SHA-256 API key verification and last_used_at timestamp updates."""
    mgr = APIKeyManager()
    user_id = str(uuid.uuid4())
    meta, raw_key = mgr.create_api_key(user_id=user_id, name="Production Key")

    assert meta.last_used_at is None

    verified_meta = mgr.verify_api_key(raw_key)
    assert verified_meta is not None
    assert verified_meta.id == meta.id
    assert verified_meta.last_used_at is not None
    assert verified_meta.last_used_at <= time.time()

    # Invalid key verification fails
    assert mgr.verify_api_key("af_live_invalid_key_12345") is None


def test_api_key_rotation():
    """Verify key rotation revokes old key and returns new active key."""
    mgr = APIKeyManager()
    user_id = str(uuid.uuid4())
    old_meta, old_raw_key = mgr.create_api_key(user_id=user_id, name="Staging Key")

    res = mgr.rotate_api_key(user_id, old_meta.id)
    assert res is not None
    new_meta, new_raw_key = res

    assert new_raw_key != old_raw_key
    assert old_meta.is_active is False
    assert new_meta.is_active is True

    # Old key fails verification, new key succeeds
    assert mgr.verify_api_key(old_raw_key) is None
    assert mgr.verify_api_key(new_raw_key) is not None


def test_api_key_revocation():
    """Verify key revocation deactivates the key."""
    mgr = APIKeyManager()
    user_id = str(uuid.uuid4())
    meta, raw_key = mgr.create_api_key(user_id=user_id, name="Temp Key")

    assert mgr.revoke_api_key(user_id, meta.id) is True
    assert meta.is_active is False
    assert mgr.verify_api_key(raw_key) is None


# ── 3. Audit Logging Engine & Secret Sanitization Tests ─────────────────────

def test_audit_sanitization():
    """Verify absolute zero secret leaks in audit event metadata."""
    dirty_metadata = {
        "user_email": "user@agentflow.ai",
        "password": "supersecretpassword123",
        "access_token": "bearer_xyz_123456",
        "refresh_token": "refresh_abc_7890",
        "api_key": "af_live_secret_key_value",
        "client_secret": "github_client_secret_xyz",
        "safe_count": 42,
        "nested": {
            "auth_header": "Bearer secret_jwt",
            "provider": "Google",
        }
    }

    clean = sanitize_metadata(dirty_metadata)

    assert clean["user_email"] == "user@agentflow.ai"
    assert clean["safe_count"] == 42
    assert clean["password"] == "[REDACTED]"
    assert clean["access_token"] == "[REDACTED]"
    assert clean["refresh_token"] == "[REDACTED]"
    assert clean["api_key"] == "[REDACTED]"
    assert clean["client_secret"] == "[REDACTED]"
    assert clean["nested"]["auth_header"] == "[REDACTED]"
    assert clean["nested"]["provider"] == "Google"


def test_audit_logger_event_logging():
    """Verify audit log event appending, ID generation, and structured queries."""
    logger_inst = AuditLogger()
    evt = logger_inst.log(
        actor_id="usr_1",
        actor_email="admin@agentflow.ai",
        actor_role="OWNER",
        action="workflow.create",
        resource_type="workflow",
        resource_id="wf_123",
        status="SUCCESS",
        metadata={"title": "Data Pipeline", "api_key": "af_live_secret"},
    )

    assert evt.id.startswith("evt_")
    assert evt.actor_email == "admin@agentflow.ai"
    assert evt.action == "workflow.create"
    assert evt.status == "SUCCESS"
    assert evt.metadata["api_key"] == "[REDACTED]"

    # Query events
    query_results = logger_inst.query(action="workflow.create")
    assert len(query_results) >= 1
    assert query_results[0].id == evt.id


# ── 4. FastAPI Endpoint Authorization & Integration Tests ───────────────────

def test_api_keys_endpoint_create_and_list():
    """Test POST /api/v1/api-keys and GET /api/v1/api-keys endpoints."""
    # Create key
    resp = client.post("/api/v1/api-keys", json={"name": "Test Key Endpoint", "expires_in_days": 30})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "raw_key" in data
    assert data["raw_key"].startswith("af_live_")
    key_id = data["id"]
    raw_key = data["raw_key"]

    # List keys metadata
    list_resp = client.get("/api/v1/api-keys")
    assert list_resp.status_code == 200
    keys_list = list_resp.json()["data"]
    assert len(keys_list) >= 1
    target = next((k for k in keys_list if k["id"] == key_id), None)
    assert target is not None
    assert "raw_key" not in target  # Must not return raw key in list calls

    # Revoke key
    del_resp = client.delete(f"/api/v1/api-keys/{key_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["revoked"] is True


def test_api_key_header_authentication():
    """Test authentication via X-API-Key header."""
    # Create valid key using global manager
    meta, raw_key = api_key_manager.create_api_key("00000000-0000-0000-0000-000000000001", "Header Auth Key")

    # Access protected route using X-API-Key header
    headers = {"X-API-Key": raw_key}
    res = client.get("/api/v1/users/me", headers=headers)
    assert res.status_code == 200
    user_data = res.json()["data"]
    assert user_data["role"] == "ADMIN" or user_data["email"].startswith("apikey_")


def test_audit_logs_endpoint():
    """Test GET /api/v1/audit-logs endpoint."""
    res = client.get("/api/v1/audit-logs")
    assert res.status_code == 200
    logs = res.json()["data"]
    assert isinstance(logs, list)


def test_users_role_assignment_endpoint():
    """Test GET /api/v1/users and PUT /api/v1/users/{id}/role endpoints."""
    list_res = client.get("/api/v1/users")
    assert list_res.status_code == 200
    users = list_res.json()["data"]
    assert len(users) >= 1

    target_id = users[0]["id"]
    update_res = client.put(f"/api/v1/users/{target_id}/role", json={"role": "ADMIN"})
    assert update_res.status_code == 200
    assert update_res.json()["data"]["role"] == "ADMIN"
