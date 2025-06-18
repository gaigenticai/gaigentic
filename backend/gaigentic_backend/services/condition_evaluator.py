"""Utilities to safely evaluate workflow conditions."""
from __future__ import annotations

import ast
from typing import Any, Dict


_ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Subscript,
    ast.Attribute,
    ast.List,
    ast.Tuple,
    ast.Dict,
)


def _validate_ast(expr: str) -> ast.Expression:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:  # pragma: no cover - runtime path
        raise ValueError("invalid expression") from exc
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_AST_NODES):
            raise ValueError("disallowed expression element")
        if isinstance(node, ast.Call):
            raise ValueError("function calls not allowed")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError("private attributes not allowed")
    return tree


def evaluate_condition(expr: str | None, context: Dict[str, Any]) -> bool:
    """Evaluate a condition expression in a restricted context."""
    if not expr:
        return True
    if len(expr) > 500:
        raise ValueError("expression too long")
    if any(x in expr for x in ("import", "open", "eval")):
        raise ValueError("potentially unsafe expression")
    tree = _validate_ast(expr)
    try:
        return bool(eval(compile(tree, "<condition>", "eval"), {}, context))
    except Exception as exc:  # pragma: no cover - runtime errors
        raise ValueError("error evaluating expression") from exc
