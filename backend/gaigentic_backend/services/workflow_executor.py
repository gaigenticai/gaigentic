"""Runtime execution of stored agent workflows."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, AsyncGenerator
from uuid import UUID

from fastapi import HTTPException, status

from ..database import SessionLocal
from ..models.agent import Agent
from ..schemas.chat import WorkflowDraft, Edge, Node
from .memory_adapter import fetch_context_for_agent
from .tool_executor import execute_tool
from .condition_evaluator import evaluate_condition

logger = logging.getLogger(__name__)


async def _load_agent(agent_id: UUID, tenant_id: UUID) -> Agent:
    async with SessionLocal() as session:  # type: AsyncSession
        agent = await session.get(Agent, agent_id)
        if agent is None or agent.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        return agent


def _topological_order(draft: WorkflowDraft) -> List[str]:
    node_map = {n.id: n for n in draft.nodes}
    incoming: Dict[str, int] = {n.id: 0 for n in draft.nodes}
    adjacency: Dict[str, List[str]] = {}
    for edge in draft.edges:
        if edge.source not in node_map or edge.target not in node_map:
            raise HTTPException(status_code=400, detail="Workflow references unknown node")
        adjacency.setdefault(edge.source, []).append(edge.target)
        incoming[edge.target] += 1
    queue = [nid for nid, inc in incoming.items() if inc == 0]
    order: List[str] = []
    while queue:
        nid = queue.pop(0)
        order.append(nid)
        for tgt in adjacency.get(nid, []):
            incoming[tgt] -= 1
            if incoming[tgt] == 0:
                queue.append(tgt)
    if len(order) != len(draft.nodes):
        raise HTTPException(status_code=400, detail="Workflow graph has cycle")
    return order


async def run_workflow_stream(
    agent_id: UUID, input_context: Dict[str, Any], tenant_id: UUID
) -> AsyncGenerator[Dict[str, Any], None]:
    """Yield workflow execution results step by step."""

    agent = await _load_agent(agent_id, tenant_id)

    workflow_data = (agent.config or {}).get("workflow")
    if not workflow_data:
        raise HTTPException(status_code=400, detail="Workflow not defined")

    try:
        draft = WorkflowDraft.model_validate(workflow_data)
    except Exception as exc:  # pragma: no cover - runtime validation
        logger.exception("Invalid workflow data: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid workflow") from exc

    order = _topological_order(draft)
    if len(order) > 25:
        raise HTTPException(status_code=400, detail="Workflow exceeds step limit")

    use_memory = bool((agent.config or {}).get("use_memory"))
    memory_context: Dict[str, Any] = {}
    if use_memory:
        memory_context = await fetch_context_for_agent(agent_id)

    node_map: Dict[str, Node] = {n.id: n for n in draft.nodes}
    edges_by_source: Dict[str, List[Edge]] = {}
    edges_by_target: Dict[str, List[Edge]] = {}
    for e in draft.edges:
        edges_by_source.setdefault(e.source, []).append(e)
        edges_by_target.setdefault(e.target, []).append(e)

    results: Dict[str, Any] = {}
    triggered: Dict[str, List[str]] = {}

    for node_id in order:
        node = node_map[node_id]
        incoming = edges_by_target.get(node_id, [])
        upstream_ids = triggered.get(node_id, [])
        upstream = {sid: results[sid] for sid in upstream_ids}

        if incoming and not upstream:
            yield {"node_id": node_id, "status": "skipped", "reason": "no_upstream"}
            continue

        cond_ctx = {"context": input_context, "memory": memory_context, "upstream": upstream}
        try:
            if not evaluate_condition(node.condition, cond_ctx):
                yield {"node_id": node_id, "status": "skipped", "reason": "condition"}
                continue
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid node condition")

        step_input = {
            "context": input_context,
            "memory": memory_context,
            "upstream": upstream,
            "config": node.data or {},
        }
        agent_override = node.agent_id or agent_id
        logger.info("Executing node %s (%s) using agent %s", node_id, node.type, agent_override)
        output = await execute_tool(agent_override, node.type, step_input, tenant_id)
        logger.info("Output for node %s: %s", node_id, output)
        results[node_id] = output
        for edge in edges_by_source.get(node_id, []):
            try:
                if not evaluate_condition(edge.condition, {"output": output}):
                    continue
            except ValueError:
                logger.error("Invalid edge condition on %s", edge.id)
                continue
            triggered.setdefault(edge.target, []).append(node_id)

        yield {
            "node_id": node_id,
            "tool": node.type,
            "output": output,
            "status": "success",
        }


async def run_workflow(agent_id: UUID, input_context: Dict[str, Any], tenant_id: UUID) -> Dict[str, Any]:
    """Execute the stored workflow for an agent and return consolidated result."""

    results: Dict[str, Any] = {}
    async for step in run_workflow_stream(agent_id, input_context, tenant_id):
        results[step["node_id"]] = step["output"]

    return {"steps": results, "status": "complete"}
