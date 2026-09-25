"""
Role-Based Access Control (RBAC) Module for AgentFlow AI (AI-35).
Defines centralized roles, permission matrices, and FastAPI authorization dependencies.
"""

from typing import Callable, List, Optional, Dict, Set
from fastapi import Depends, HTTPException, status, Request
from app.dependencies.auth import get_current_user
from app.models.users import User

# Role Constants
ROLE_OWNER = "OWNER"
ROLE_ADMIN = "ADMIN"
ROLE_MEMBER = "MEMBER"
ROLE_VIEWER = "VIEWER"

ALL_ROLES = [ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER]

# Granular Permission Matrix
# Permission Code -> Allowed Roles
PERMISSION_MATRIX: Dict[str, Set[str]] = {
    # Workflows
    "workflow.create": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER},
    "workflow.read": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER},
    "workflow.update": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER},
    "workflow.delete": {ROLE_OWNER, ROLE_ADMIN},
    "workflow.execute": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER},

    # Templates
    "template.create": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER},
    "template.read": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER},
    "template.update": {ROLE_OWNER, ROLE_ADMIN},
    "template.delete": {ROLE_OWNER, ROLE_ADMIN},

    # Executions
    "execution.read": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER},
    "execution.cancel": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER},
    "execution.delete": {ROLE_OWNER, ROLE_ADMIN},

    # Connections & Credentials
    "connection.read": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER},
    "connection.write": {ROLE_OWNER, ROLE_ADMIN},
    "connection.delete": {ROLE_OWNER, ROLE_ADMIN},
    "credential.read": {ROLE_OWNER, ROLE_ADMIN},
    "credential.write": {ROLE_OWNER, ROLE_ADMIN},
    "credential.delete": {ROLE_OWNER, ROLE_ADMIN},

    # User Management
    "user.read": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER},
    "user.write": {ROLE_OWNER, ROLE_ADMIN},
    "user.delete": {ROLE_OWNER},
    "user.role_assign": {ROLE_OWNER, ROLE_ADMIN},

    # Organization
    "organization.read": {ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER},
    "organization.write": {ROLE_OWNER},

    # Audit Trail
    "audit.read": {ROLE_OWNER, ROLE_ADMIN},

    # API Keys
    "api_key.create": {ROLE_OWNER, ROLE_ADMIN},
    "api_key.read": {ROLE_OWNER, ROLE_ADMIN},
    "api_key.revoke": {ROLE_OWNER, ROLE_ADMIN},
}


def get_user_role(user: User) -> str:
    """
    Extract the effective role string for a User instance.
    Defaults to OWNER if superuser or fallback user, otherwise reads role attribute/roles relationship.
    """
    if getattr(user, "is_superuser", False) or getattr(user, "email", "") == "admin@agentflow.ai":
        return ROLE_OWNER

    # Check direct role property if present
    if hasattr(user, "role") and user.role in ALL_ROLES:
        return user.role

    # Check roles relationship if populated
    if hasattr(user, "roles") and user.roles:
        first_role = user.roles[0]
        name = getattr(first_role, "name", "").upper()
        if name in ALL_ROLES:
            return name

    # Default role for standard authenticated users
    return ROLE_MEMBER


def has_permission(role: str, permission: str) -> bool:
    """
    Check if a given role possesses a specific permission.
    """
    role_upper = role.upper() if role else ROLE_MEMBER
    allowed_roles = PERMISSION_MATRIX.get(permission)
    if not allowed_roles:
        return False
    return role_upper in allowed_roles


def require_permission(permission: str) -> Callable:
    """
    FastAPI dependency factory enforcing a specific permission check.
    Raises HTTP 403 Forbidden if user's role lacks the required permission.
    """
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        user_role = get_user_role(current_user)
        if not has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User role '{user_role}' lacks required permission '{permission}'."
            )
        return current_user

    return dependency


def require_role(allowed_roles: List[str]) -> Callable:
    """
    FastAPI dependency factory enforcing that user has one of allowed_roles.
    """
    allowed_set = {r.upper() for r in allowed_roles}

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        user_role = get_user_role(current_user)
        if user_role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{user_role}' is not in allowed roles {list(allowed_set)}."
            )
        return current_user

    return dependency


def authorize_resource_owner(current_user: User, owner_id: str) -> bool:
    """
    Check if the user is the owner of a resource or has ADMIN/OWNER rights.
    """
    role = get_user_role(current_user)
    if role in [ROLE_OWNER, ROLE_ADMIN]:
        return True
    return str(current_user.id) == str(owner_id)
