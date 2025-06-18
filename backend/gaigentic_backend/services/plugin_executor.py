from __future__ import annotations

import asyncio
import builtins
import json
import logging
import re
from types import MappingProxyType
from typing import Any, Dict

logger = logging.getLogger(__name__)

FORBIDDEN_RE = re.compile(r"\b(import|os|sys|open|subprocess|socket|eval|exec)\b")

SAFE_BUILTINS = MappingProxyType({
    name: getattr(builtins, name)
    for name in [
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "float",
        "int",
        "len",
        "list",
        "max",
        "min",
        "range",
        "str",
        "sum",
        "enumerate",
        "zip",
        "sorted",
    ]
})


async def run_plugin(code: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute plugin code safely and return result."""

    if FORBIDDEN_RE.search(code):
        raise ValueError("disallowed keywords present")
    try:
        compiled = compile(code, "<plugin>", "exec")
    except SyntaxError as exc:
        raise ValueError("syntax error") from exc

    def _exec() -> Dict[str, Any]:
        scope = {"__builtins__": SAFE_BUILTINS, "input": input_data, "output": None}
        exec(compiled, scope)
        result = scope.get("output")
        if isinstance(result, dict):
            return result
        return {"result": result}

    try:
        result = await asyncio.wait_for(asyncio.to_thread(_exec), timeout=10)
    except asyncio.TimeoutError as exc:
        raise TimeoutError("plugin timed out") from exc

    try:
        text = json.dumps(result)
    except Exception:
        text = str(result)
    if len(text) > 1000:
        text = text[:1000] + "..."
    logger.info("Plugin executed with output: %s", text)
    return result
