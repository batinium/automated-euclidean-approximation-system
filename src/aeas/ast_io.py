"""Serialization between AEAS expression trees and CANB AST dictionaries."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from .canonicalize import canonicalize
from .expr import ExprNode, Op
from .schema_validation import SchemaValidationError, validate_instance


class AstValidationError(ValueError):
    """Raised when a CANB AST cannot be parsed into an expression tree."""


_BINARY_AST_TO_OP = {
    "ADD": Op.ADD,
    "SUB": Op.SUB,
    "MUL": Op.MUL,
    "DIV": Op.DIV,
}

_OP_TO_BINARY_AST = {
    Op.ADD: "ADD",
    Op.SUB: "SUB",
    Op.MUL: "MUL",
    Op.DIV: "DIV",
}


def expr_to_ast(expr: ExprNode) -> dict[str, Any]:
    """Convert an :class:`ExprNode` into a CANB ``aeas-ast-v1`` node."""
    if not isinstance(expr, ExprNode):
        raise AstValidationError(f"expected ExprNode, got {type(expr).__name__}")

    if expr.op == Op.CONST:
        if expr.value is None:
            raise AstValidationError("CONST node has no value")
        return {"op": "CONST", "value": _fraction_to_wire(expr.value)}

    if expr.op == Op.SQRT:
        _check_arity(expr, 1)
        return {"op": "SQRT", "args": [expr_to_ast(expr.children[0])]}

    if expr.op in _OP_TO_BINARY_AST:
        _check_arity(expr, 2)
        return {
            "op": _OP_TO_BINARY_AST[expr.op],
            "args": [
                expr_to_ast(expr.children[0]),
                expr_to_ast(expr.children[1]),
            ],
        }

    raise AstValidationError(f"unsupported expression op {expr.op!r}")


def ast_to_expr(ast_dict: dict[str, Any]) -> ExprNode:
    """Parse a CANB AST node into an :class:`ExprNode`.

    ``NEG`` and ``INV`` are accepted on the wire and lowered to ``0 - x`` and
    ``1 / x`` because the existing AEAS core has no unary op variants.
    """
    try:
        validate_instance(ast_dict, "ast.schema.json")
    except SchemaValidationError as exc:
        raise AstValidationError(str(exc)) from exc

    try:
        return _ast_to_expr_unchecked(ast_dict)
    except (KeyError, TypeError, ValueError) as exc:
        raise AstValidationError(f"invalid AST node {ast_dict!r}: {exc}") from exc


def canonicalize_ast(ast: dict[str, Any]) -> dict[str, Any]:
    """Parse, canonicalize with AEAS rules, and re-serialize a CANB AST."""
    return expr_to_ast(canonicalize(ast_to_expr(ast)))


def _ast_to_expr_unchecked(ast: dict[str, Any]) -> ExprNode:
    op = ast["op"]
    if op == "CONST":
        return ExprNode(Op.CONST, value=_parse_rational(ast["value"]))

    args = ast["args"]
    if op == "NEG":
        return ExprNode(
            Op.SUB,
            children=(
                ExprNode(Op.CONST, value=Fraction(0)),
                _ast_to_expr_unchecked(args[0]),
            ),
        )
    if op == "INV":
        return ExprNode(
            Op.DIV,
            children=(
                ExprNode(Op.CONST, value=Fraction(1)),
                _ast_to_expr_unchecked(args[0]),
            ),
        )
    if op == "SQRT":
        return ExprNode(Op.SQRT, children=(_ast_to_expr_unchecked(args[0]),))
    if op in _BINARY_AST_TO_OP:
        return ExprNode(
            _BINARY_AST_TO_OP[op],
            children=(
                _ast_to_expr_unchecked(args[0]),
                _ast_to_expr_unchecked(args[1]),
            ),
        )

    raise AstValidationError(f"unsupported AST op {op!r}")


def _parse_rational(raw: str) -> Fraction:
    num, den = raw.split("/", 1)
    return Fraction(int(num), int(den))


def _fraction_to_wire(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _check_arity(expr: ExprNode, expected: int) -> None:
    actual = len(expr.children)
    if actual != expected:
        raise AstValidationError(
            f"{expr.op.name} expected {expected} children, got {actual}"
        )
