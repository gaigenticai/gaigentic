"""Utilities to validate workflow drafts."""
from __future__ import annotations

import logging
from typing import Set

from ..schemas.chat import WorkflowDraft

logger = logging.getLogger(__name__)


def validate_workflow(draft: WorkflowDraft) -> None:
    """Validate basic workflow structure."""

    node_ids: Set[str] = set()
    for node in draft.nodes:
        if node.id in node_ids:
            logger.error("Duplicate node id detected: %s", node.id)
            raise ValueError(f"duplicate node id {node.id}")
        node_ids.add(node.id)

    for edge in draft.edges:
        if edge.source not in node_ids or edge.target not in node_ids:
            logger.error("Edge %s has missing endpoints", edge.id)
            raise ValueError(f"edge {edge.id} references missing nodes")
