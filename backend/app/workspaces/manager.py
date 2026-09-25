import logging
import time
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field
from app.runtime.exceptions import RuntimeException

logger = logging.getLogger("agentflow.workspaces")


class WorkspaceRole(str, Enum):
    OWNER = "Owner"
    ADMIN = "Admin"
    EDITOR = "Editor"
    VIEWER = "Viewer"


class WorkspaceMemberModel(BaseModel):
    user_id: str
    email: str
    role: WorkspaceRole
    joined_at: float = Field(default_factory=time.time)


class WorkspaceModel(BaseModel):
    id: str
    name: str
    organization: str = "Enterprise Org"
    members: Dict[str, WorkspaceMemberModel] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


class WorkspaceManager:
    """Enterprise Workspace Manager & RBAC Enforcer."""

    ROLE_PERMISSIONS: Dict[WorkspaceRole, Set[str]] = {
        WorkspaceRole.OWNER: {
            "workflow:create", "workflow:edit", "workflow:delete", "workflow:publish",
            "oauth:manage", "templates:manage", "users:manage", "billing:manage",
        },
        WorkspaceRole.ADMIN: {
            "workflow:create", "workflow:edit", "workflow:delete", "workflow:publish",
            "oauth:manage", "templates:manage", "users:manage",
        },
        WorkspaceRole.EDITOR: {
            "workflow:create", "workflow:edit", "workflow:publish",
        },
        WorkspaceRole.VIEWER: set(),
    }

    def __init__(self) -> None:
        self._workspaces: Dict[str, WorkspaceModel] = {}
        self._seed_default_workspace()

    def _seed_default_workspace(self) -> None:
        ws_id = "ws_default"
        ws = WorkspaceModel(id=ws_id, name="Primary Enterprise Workspace")
        ws.members["usr_1"] = WorkspaceMemberModel(user_id="usr_1", email="owner@company.com", role=WorkspaceRole.OWNER)
        self._workspaces[ws_id] = ws

    async def create_workspace(self, name: str, owner_id: str, owner_email: str) -> WorkspaceModel:
        ws_id = f"ws_{name.lower().replace(' ', '_')}"
        ws = WorkspaceModel(id=ws_id, name=name)
        ws.members[owner_id] = WorkspaceMemberModel(user_id=owner_id, email=owner_email, role=WorkspaceRole.OWNER)
        self._workspaces[ws_id] = ws
        logger.info(f"Created Enterprise Workspace [{ws_id}] for owner [{owner_email}].")
        return ws

    async def check_permission(self, workspace_id: str, user_id: str, permission: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return True  # Fallback for default single tenant

        member = ws.members.get(user_id)
        if not member:
            raise RuntimeException(f"User [{user_id}] is not a member of workspace [{workspace_id}].")

        allowed_perms = self.ROLE_PERMISSIONS.get(member.role, set())
        if permission not in allowed_perms:
            raise RuntimeException(f"Access Denied: Role [{member.role.value}] lacks permission [{permission}].")

        return True


workspace_manager = WorkspaceManager()
