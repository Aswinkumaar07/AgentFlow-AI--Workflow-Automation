import logging
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.marketplace")


class MarketplaceComment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_name: str
    content: str
    created_at: str = "2026-08-04T15:00:00Z"


class MarketplaceTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    purpose: str
    connectors: List[str] = Field(default_factory=list)
    difficulty: str = "Intermediate"  # 'Beginner', 'Intermediate', 'Advanced'
    estimated_runtime_ms: int = 1500
    industry: str = "General"  # 'Finance', 'E-Commerce', 'Marketing', 'DevOps', 'HR', 'Engineering'
    use_cases: List[str] = Field(default_factory=list)
    author: str = "AgentFlow AI Community"
    version: str = "1.0.0"
    rating: float = 4.8
    rating_count: int = 12
    fork_count: int = 5
    workflow_graph: Dict[str, Any] = Field(default_factory=dict)
    comments: List[MarketplaceComment] = Field(default_factory=list)


class AIMarketplaceEngine:
    """
    AgentFlow AI v2.0 - AI-Powered Workflow Marketplace Engine
    Analyzes workflows, extracts metadata, provides semantic search recommendations,
    one-click AI personalization, versioning, ratings, comments, and workflow forking.
    """

    def __init__(self) -> None:
        self.templates: Dict[str, MarketplaceTemplate] = {}
        self._seed_default_marketplace()

    def _seed_default_marketplace(self) -> None:
        seed_1 = MarketplaceTemplate(
            id="tpl_hr_onboarding",
            title="Automated HR Employee Onboarding",
            description="Reads employee list from Google Sheets, loops records, and sends Gmail welcome emails.",
            purpose="Streamline HR onboarding by automating welcome emails and account setup.",
            connectors=["Google Sheets", "Loop", "Gmail"],
            difficulty="Beginner",
            estimated_runtime_ms=1200,
            industry="HR",
            use_cases=["Employee Onboarding", "Email Notifications"],
            author="AgentFlow AI",
            workflow_graph={
                "title": "Automated HR Employee Onboarding",
                "nodes": [
                    {"id": "step_1", "provider": "Google Sheets", "operation_id": "sheets.spreadsheets.values.get"},
                    {"id": "step_2", "provider": "Loop", "operation_id": "loop.process"},
                    {"id": "step_3", "provider": "Gmail", "operation_id": "gmail.messages.send"},
                ],
                "edges": [
                    {"id": "e_step_1-step_2", "source": "step_1", "target": "step_2"},
                    {"id": "e_step_2-step_3", "source": "step_2", "target": "step_3"},
                ],
            },
        )
        self.templates[seed_1.id] = seed_1

    def publish_workflow(
        self, title: str, description: str, workflow_graph: Dict[str, Any], author: str = "User"
    ) -> MarketplaceTemplate:
        nodes = workflow_graph.get("nodes", [])
        connectors = list(set([n.get("provider", "Generic") for n in nodes if n.get("provider")]))

        # AI metadata extraction logic
        difficulty = "Beginner" if len(nodes) <= 3 else "Intermediate" if len(nodes) <= 6 else "Advanced"
        est_runtime = len(nodes) * 450

        industry = "General"
        conn_str = (" ".join(connectors) + " " + title + " " + description).lower()
        if "stripe" in conn_str or "invoice" in conn_str or "payment" in conn_str or "finance" in conn_str:
            industry = "Finance"
        elif "slack" in conn_str or "github" in conn_str:
            industry = "Engineering"
        elif "sheets" in conn_str or "gmail" in conn_str:
            industry = "HR"

        tpl = MarketplaceTemplate(
            title=title,
            description=description,
            purpose=f"Automated workflow pipeline with {len(connectors)} connector(s).",
            connectors=connectors,
            difficulty=difficulty,
            estimated_runtime_ms=est_runtime,
            industry=industry,
            use_cases=["Workflow Automation", f"{industry} Operations"],
            author=author,
            workflow_graph=workflow_graph,
        )
        self.templates[tpl.id] = tpl
        logger.info(f"AI Marketplace published template '{tpl.title}' (ID: {tpl.id}).")
        return tpl

    def search_recommend(self, query: str) -> List[MarketplaceTemplate]:
        q_lower = query.lower()
        results = []
        for tpl in self.templates.values():
            if (
                q_lower in tpl.title.lower()
                or q_lower in tpl.description.lower()
                or q_lower in tpl.industry.lower()
                or any(q_lower in c.lower() for c in tpl.connectors)
            ):
                results.append(tpl)
        return results or list(self.templates.values())

    def personalize_template(
        self, template_id: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        tpl = self.templates.get(template_id)
        if not tpl:
            return {}

        graph = {**tpl.workflow_graph, "is_personalized": True}
        user_email = user_context.get("email", "user@company.com")
        user_company = user_context.get("company", "Company")

        # Mutate graph node parameters with personalized user context
        for node in graph.get("nodes", []):
            params = {**node.get("parameters", {})}
            if node.get("provider") == "Gmail":
                params["recipient"] = user_email
                params["subject"] = f"Welcome to {user_company}"
            node["parameters"] = params

        return graph

    def fork_workflow(self, template_id: str, user_id: str = "User") -> MarketplaceTemplate:
        tpl = self.templates.get(template_id)
        if not tpl:
            raise ValueError(f"Template {template_id} not found.")

        tpl.fork_count += 1
        forked_graph = {**tpl.workflow_graph, "forked_from": template_id}
        forked_tpl = MarketplaceTemplate(
            title=f"Fork of {tpl.title}",
            description=f"Forked from {tpl.title} by {user_id}",
            purpose=tpl.purpose,
            connectors=tpl.connectors,
            difficulty=tpl.difficulty,
            estimated_runtime_ms=tpl.estimated_runtime_ms,
            industry=tpl.industry,
            use_cases=tpl.use_cases,
            author=user_id,
            workflow_graph=forked_graph,
        )
        return forked_tpl

    def add_rating(self, template_id: str, stars: float) -> MarketplaceTemplate:
        tpl = self.templates.get(template_id)
        if tpl:
            total_score = tpl.rating * tpl.rating_count + stars
            tpl.rating_count += 1
            tpl.rating = round(total_score / tpl.rating_count, 1)
        return tpl

    def add_comment(self, template_id: str, user_name: str, content: str) -> MarketplaceTemplate:
        tpl = self.templates.get(template_id)
        if tpl:
            tpl.comments.append(MarketplaceComment(user_name=user_name, content=content))
        return tpl


ai_marketplace_engine = AIMarketplaceEngine()
