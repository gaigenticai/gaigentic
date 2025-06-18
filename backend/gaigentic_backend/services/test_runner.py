"""Utilities for running agent tests."""
from __future__ import annotations

import json
from typing import Any, Dict
from uuid import UUID

from deepdiff import DeepDiff

from .workflow_executor import run_workflow


async def run_test(
    agent_id: UUID, input_context: Dict[str, Any], expected_output: Dict[str, Any], tenant_id: UUID
) -> Dict[str, Any]:
    """Execute an agent workflow and compare output."""

    actual = await run_workflow(agent_id, input_context, tenant_id)
    diff_obj = DeepDiff(expected_output, actual, ignore_order=True)
    diff_dict = diff_obj.to_dict()
    lines = json.dumps(diff_dict, indent=2).splitlines()
    truncated = False
    if len(lines) > 100:
        lines = lines[:100]
        truncated = True
    diff_text = "\n".join(lines)
    result = {"status": "pass" if not diff_dict else "fail", "diff": diff_text, "actual": actual}
    if truncated:
        result["diff_truncated"] = True
    return result

