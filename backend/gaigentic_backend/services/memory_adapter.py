"""Utilities for retrieving agent memory/context."""

from __future__ import annotations

import logging
from typing import Dict
from uuid import UUID

logger = logging.getLogger(__name__)


async def fetch_context_for_agent(agent_id: UUID) -> Dict:
    """Return contextual memory for the specified agent.

    This would normally aggregate previous run data, uploaded files,
    or vector store summaries. For now it returns a static mock.
    """

    logger.debug("Fetching context for agent %s", agent_id)
    # Future implementation will query persistent storage.
    return {
        "historical_summary": "Agent has processed quarterly transactions and generated forecasts.",
        "prior_actions": ["ingested_transactions", "generated_report"],
    }
