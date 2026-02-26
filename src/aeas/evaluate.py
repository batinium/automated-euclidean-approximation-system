"""Arbitrary-precision evaluation of expression trees using mpmath.

Results are cached by ``(expression_hash, dps)`` so that recurring
sub-expressions are never re-evaluated.
"""

from __future__ import annotations

import mpmath

from .expr import ExprNode, Op

_cache: dict[tuple[int, int], mpmath.mpf | None] = {}


def evaluate(node: ExprNode, dps: int = 80) -> mpmath.mpf | None:
    """Evaluate *node* to *dps* decimal places.

    Returns ``None`` for invalid expressions (division by zero, sqrt of
    a negative value, non-finite result).
    """
    key = (hash(node), dps)
    if key in _cache:
        return _cache[key]
    with mpmath.workdps(dps + 15):
        return _eval(node, dps)


def _eval(node: ExprNode, dps: int) -> mpmath.mpf | None:
    key = (hash(node), dps)
    if key in _cache:
        return _cache[key]

    result: mpmath.mpf | None

    if node.op == Op.CONST:
        v = node.value
        result = mpmath.mpf(v.numerator) / mpmath.mpf(v.denominator)
    elif node.op == Op.SQRT:
        cv = _eval(node.children[0], dps)
        if cv is None or cv < 0:
            result = None
        else:
            result = mpmath.sqrt(cv)
    else:
        lv = _eval(node.children[0], dps)
        rv = _eval(node.children[1], dps)
        if lv is None or rv is None:
            result = None
        elif node.op == Op.ADD:
            result = lv + rv
        elif node.op == Op.SUB:
            result = lv - rv
        elif node.op == Op.MUL:
            result = lv * rv
        elif node.op == Op.DIV:
            result = None if rv == 0 else lv / rv
        else:
            result = None

    if result is not None and not mpmath.isfinite(result):
        result = None

    _cache[key] = result
    return result


def compute_target(n: int, dps: int = 80) -> mpmath.mpf:
    """Return ``cos(2*pi/n)`` to *dps* decimal places."""
    with mpmath.workdps(dps + 15):
        return +mpmath.cos(2 * mpmath.pi / n)


def clear_cache() -> None:
    """Drop all cached evaluation results (useful between test runs)."""
    _cache.clear()
