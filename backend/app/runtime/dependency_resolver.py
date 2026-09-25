import logging
from typing import Any, Dict, List, Set
from app.runtime.exceptions import DependencyCycleException

logger = logging.getLogger("agentflow.runtime.dependency_resolver")


class DependencyResolver:
    """DAG Dependency Resolver applying Kahn's Algorithm for ready node resolution and cycle detection."""

    @staticmethod
    def get_ready_nodes(steps: List[Dict[str, Any]], completed_step_ids: Set[str]) -> List[Dict[str, Any]]:
        """Returns nodes whose upstream dependencies are 100% satisfied."""
        ready: List[Dict[str, Any]] = []

        for step in steps:
            step_id = step.get("step_id") or step.get("id")
            if step_id in completed_step_ids:
                continue

            dependencies = step.get("dependencies") or []
            if all(dep in completed_step_ids for dep in dependencies):
                ready.append(step)

        return ready

    @staticmethod
    def validate_dag(steps: List[Dict[str, Any]]) -> List[str]:
        """Validates that DAG steps form a valid Acyclic Directed Graph (topological order)."""
        in_degree: Dict[str, int] = {}
        graph: Dict[str, List[str]] = {}

        for step in steps:
            s_id = step.get("step_id") or step.get("id")
            in_degree[s_id] = 0
            graph[s_id] = []

        for step in steps:
            s_id = step.get("step_id") or step.get("id")
            deps = step.get("dependencies") or []
            for dep in deps:
                if dep in graph:
                    graph[dep].append(s_id)
                    in_degree[s_id] += 1

        queue = [node for node, deg in in_degree.items() if deg == 0]
        topological_order: List[str] = []

        while queue:
            node = queue.pop(0)
            topological_order.append(node)
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topological_order) != len(steps):
            raise DependencyCycleException("Cycle or invalid dependency detected in workflow DAG definition.")

        return topological_order


dependency_resolver = DependencyResolver()
