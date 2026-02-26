"""Expression canonicalization: constant folding, identity elimination,
and commutative child sorting."""

from __future__ import annotations

import math
from fractions import Fraction

from .expr import ExprNode, Op

_ZERO = Fraction(0)
_ONE = Fraction(1)


def canonicalize(node: ExprNode) -> ExprNode:
    """Return the canonical form of *node*.

    1. Recursively canonicalize children.
    2. Fold expressions where every operand is a rational constant.
    3. Eliminate trivial identities (x+0, x*1, x*0, x/1, x-0).
    4. Sort children of commutative ops (ADD, MUL) by stable string key.
    """
    if node.op == Op.CONST:
        return node

    children = tuple(canonicalize(c) for c in node.children)
    op = node.op

    # -- constant folding --
    if all(c.op == Op.CONST for c in children):
        folded = _fold_constants(op, children)
        if folded is not None:
            return folded

    # -- identity simplification --
    simplified = _simplify(op, children)
    if simplified is not None:
        return simplified

    # -- commutative sorting --
    if op in (Op.ADD, Op.MUL) and len(children) == 2:
        a, b = children
        if a.to_str() > b.to_str():
            children = (b, a)

    return ExprNode(op, children=children)


# -------------------------------------------------------------------
# helpers
# -------------------------------------------------------------------


def _is_perfect_square(n: int) -> bool:
    if n < 0:
        return False
    r = math.isqrt(n)
    return r * r == n


def _fold_constants(
    op: Op, children: tuple[ExprNode, ...]
) -> ExprNode | None:
    """Evaluate an expression whose operands are all rational constants.

    Returns a CONST node on success, ``None`` when folding is impossible
    or invalid (e.g. division by zero, irrational sqrt).
    """
    if op == Op.SQRT:
        v = children[0].value
        if v < 0:
            return None
        if v == _ZERO:
            return ExprNode(Op.CONST, value=_ZERO)
        if v == _ONE:
            return ExprNode(Op.CONST, value=_ONE)
        num, den = abs(v.numerator), v.denominator
        if _is_perfect_square(num) and _is_perfect_square(den):
            return ExprNode(
                Op.CONST,
                value=Fraction(math.isqrt(num), math.isqrt(den)),
            )
        return None  # irrational — keep symbolic

    a, b = children[0].value, children[1].value
    if op == Op.ADD:
        return ExprNode(Op.CONST, value=a + b)
    if op == Op.SUB:
        return ExprNode(Op.CONST, value=a - b)
    if op == Op.MUL:
        return ExprNode(Op.CONST, value=a * b)
    if op == Op.DIV:
        if b == _ZERO:
            return None
        return ExprNode(Op.CONST, value=a / b)
    return None


def _simplify(
    op: Op, children: tuple[ExprNode, ...]
) -> ExprNode | None:
    """Eliminate trivial identity patterns.  Returns ``None`` when no
    simplification applies."""
    if op == Op.ADD:
        a, b = children
        if a.op == Op.CONST and a.value == _ZERO:
            return b
        if b.op == Op.CONST and b.value == _ZERO:
            return a

    elif op == Op.SUB:
        _a, b = children
        if b.op == Op.CONST and b.value == _ZERO:
            return _a

    elif op == Op.MUL:
        a, b = children
        if a.op == Op.CONST and a.value == _ZERO:
            return ExprNode(Op.CONST, value=_ZERO)
        if b.op == Op.CONST and b.value == _ZERO:
            return ExprNode(Op.CONST, value=_ZERO)
        if a.op == Op.CONST and a.value == _ONE:
            return b
        if b.op == Op.CONST and b.value == _ONE:
            return a

    elif op == Op.DIV:
        a, b = children
        if b.op == Op.CONST and b.value == _ONE:
            return a

    elif op == Op.SQRT:
        a = children[0]
        if a.op == Op.CONST:
            if a.value == _ZERO:
                return ExprNode(Op.CONST, value=_ZERO)
            if a.value == _ONE:
                return ExprNode(Op.CONST, value=_ONE)

    return None
