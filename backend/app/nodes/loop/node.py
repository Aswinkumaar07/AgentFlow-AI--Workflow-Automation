import logging
from typing import Any, Dict, List
from app.nodes.expression_engine import expression_engine

logger = logging.getLogger("agentflow.nodes.loop")


class LoopNode:
    """Loop DAG Node iterating across collections and exposing $loop.index, $loop.item, $loop.total."""

    @staticmethod
    def process_loop(node_params: Dict[str, Any], scope: Dict[str, Any]) -> Dict[str, Any]:
        collection_expr = node_params.get("collection", "{{$node.Sheets.values}}")
        raw_collection = expression_engine.evaluate(str(collection_expr), scope)

        items: List[Any] = []
        if isinstance(raw_collection, list):
            items = raw_collection
        elif isinstance(raw_collection, dict):
            items = list(raw_collection.values())
        elif raw_collection:
            items = [raw_collection]

        iterations = []
        total = len(items)

        for idx, item in enumerate(items):
            loop_context = {
                "$loop": {
                    "index": idx,
                    "item": item,
                    "total": total,
                    "is_first": idx == 0,
                    "is_last": idx == total - 1,
                }
            }
            iterations.append(loop_context)

        logger.info(f"LoopNode processed collection of {total} items.")

        return {
            "total_items": total,
            "iterations": iterations,
            "items": items,
        }
