import uuid
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.workflows import WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowResponse
from app.schemas.common import PaginatedResponse
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.workflows import Workflow

def parse_workflow_uuid(wf_id_str: str) -> uuid.UUID:
    """Parses a valid UUID string or generates a deterministic UUIDv5 for string identifiers."""
    try:
        return uuid.UUID(wf_id_str)
    except Exception:
        return uuid.uuid5(uuid.NAMESPACE_DNS, wf_id_str)

async def resolve_canonical_workflow_id(workflow_id_str: str, db: Optional[AsyncSession] = None) -> str:
    """Resolves a workflow identifier (which may be a database UUID or string ID) to its canonical storage string ID.

    If given a UUID, queries the workflow definition in the database to extract the underlying
    workflow_id (e.g. 'wf_studio_1' or 'wf_gen_...'). If not a UUID or if no record is found, returns workflow_id_str.
    """
    if not workflow_id_str:
        return "wf_studio_1"

    # Only attempt database lookup if the string is formatted as a valid UUID
    try:
        wf_uuid = uuid.UUID(workflow_id_str)
    except Exception:
        return workflow_id_str

    import json
    if db is not None:
        try:
            repo = WorkflowRepository(db)
            wf = await repo.get_by_id(wf_uuid)
            if wf and wf.definition:
                def_data = wf.definition if isinstance(wf.definition, dict) else json.loads(wf.definition or "{}")
                canon_id = def_data.get("workflow_id")
                if canon_id and isinstance(canon_id, str):
                    return canon_id
        except Exception:
            pass
    else:
        try:
            from app.database.session import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                repo = WorkflowRepository(session)
                wf = await repo.get_by_id(wf_uuid)
                if wf and wf.definition:
                    def_data = wf.definition if isinstance(wf.definition, dict) else json.loads(wf.definition or "{}")
                    canon_id = def_data.get("workflow_id")
                    if canon_id and isinstance(canon_id, str):
                        return canon_id
        except Exception:
            pass

    return workflow_id_str

class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.workflow_repo = WorkflowRepository(db)

    async def create_workflow(self, user_id: uuid.UUID, req: WorkflowCreateRequest) -> WorkflowResponse:
        data = req.model_dump()
        data["owner_id"] = user_id
        data["status"] = "active"
        workflow = await self.workflow_repo.create(data)
        return WorkflowResponse.model_validate(workflow)

    async def register_or_update_workflow(
        self,
        user_id: uuid.UUID,
        workflow_id_str: str,
        title: str,
        description: Optional[str] = None,
        definition: Optional[dict] = None,
        version: int = 1,
        trigger_type: str = "manual",
        status: str = "active",
    ) -> WorkflowResponse:
        """Registers a new workflow entity in SQL DB or updates an existing entity without duplicating rows."""
        wf_uuid = parse_workflow_uuid(workflow_id_str)
        existing = await self.workflow_repo.get_by_id(wf_uuid)
        if existing:
            if existing.owner_id != user_id:
                raise ForbiddenException(message="You do not have access to modify this workflow")
            update_data = {
                "title": title or existing.title,
                "description": description if description is not None else existing.description,
                "definition": definition if definition is not None else existing.definition,
                "version": max(version, existing.version),
                "trigger_type": trigger_type or existing.trigger_type,
                "status": status or existing.status,
            }
            updated = await self.workflow_repo.update(existing, update_data)
            return WorkflowResponse.model_validate(updated)
        else:
            new_data = {
                "id": wf_uuid,
                "title": title or f"Workflow {workflow_id_str}",
                "description": description or "",
                "status": status,
                "version": version,
                "definition": definition or {},
                "trigger_type": trigger_type,
                "owner_id": user_id,
            }
            created = await self.workflow_repo.create(new_data)
            return WorkflowResponse.model_validate(created)

    async def list_workflows(self, user_id: uuid.UUID, page: int = 1, page_size: int = 20) -> PaginatedResponse[WorkflowResponse]:
        skip = (page - 1) * page_size
        workflows = await self.workflow_repo.get_by_owner(owner_id=user_id, skip=skip, limit=page_size)
        total = await self.workflow_repo.count_by_owner(owner_id=user_id)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        items = [WorkflowResponse.model_validate(w) for w in workflows]
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_workflow_details(self, user_id: uuid.UUID, workflow_id: uuid.UUID) -> WorkflowResponse:
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundException(message="Workflow not found")
        if workflow.owner_id != user_id:
            raise ForbiddenException(message="You do not have access to this workflow")
        return WorkflowResponse.model_validate(workflow)

    async def update_workflow(self, user_id: uuid.UUID, workflow_id: uuid.UUID, req: WorkflowUpdateRequest) -> WorkflowResponse:
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundException(message="Workflow not found")
        if workflow.owner_id != user_id:
            raise ForbiddenException(message="You do not have access to modify this workflow")

        updated = await self.workflow_repo.update(workflow, req.model_dump(exclude_unset=True))
        return WorkflowResponse.model_validate(updated)

    async def delete_workflow(self, user_id: uuid.UUID, workflow_id: uuid.UUID) -> bool:
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundException(message="Workflow not found")
        if workflow.owner_id != user_id:
            raise ForbiddenException(message="You do not have access to delete this workflow")

        return await self.workflow_repo.soft_delete(workflow_id)
