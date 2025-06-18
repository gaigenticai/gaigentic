"""Translate workflow drafts to Superagent format."""
from __future__ import annotations

from typing import Dict, List
import logging

from ..schemas.chat import WorkflowDraft
from .flow_validator import validate_workflow

logger = logging.getLogger(__name__)

_ALLOWED_TOOLS = {
    "kyc_verification",
    "fraud_detection",
    "document_analysis",
    "cash_forecast",
    "recommend_action",
}


def translate_to_superagent(draft: WorkflowDraft) -> Dict:
    """Convert a ``WorkflowDraft`` to Superagent JSON format."""

    validate_workflow(draft)

    node_map = {n.id: n for n in draft.nodes}
    incoming: Dict[str, int] = {n.id: 0 for n in draft.nodes}
    for edge in draft.edges:
        if edge.target in incoming:
            incoming[edge.target] += 1
        else:
            raise ValueError(f"edge {edge.id} references unknown node")

    entry_nodes = [nid for nid, count in incoming.items() if count == 0]
    if len(entry_nodes) != 1:
        raise ValueError("workflow must have exactly one entry node")

    for node in draft.nodes:
        if node.type not in _ALLOWED_TOOLS:
            raise ValueError(f"unknown tool {node.type}")

    edges_by_source: Dict[str, List[str]] = {}
    for edge in draft.edges:
        edges_by_source.setdefault(edge.source, []).append(edge.target)

    steps = []
    for node in draft.nodes:
        steps.append(
            {
                "id": node.id,
                "tool": node.type,
                "config": node.data,
                "next": edges_by_source.get(node.id, []),
            }
        )

    superagent_json = {"entrypoint": entry_nodes[0], "steps": steps}
    logger.debug("Translated workflow: %s", superagent_json)
    return superagent_json
