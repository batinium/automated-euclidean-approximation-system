"""PSLQ baseline for CANB."""

from __future__ import annotations

import math
import time
from fractions import Fraction
from typing import Any

import mpmath

from aeas.ast_io import expr_to_ast
from aeas.canb_targets import target_from_spec
from aeas.canonicalize import canonicalize
from aeas.evaluate import clear_cache, evaluate
from aeas.expr import ExprNode, Op
from aeas.schema_validation import validate_instance


SUBMITTED_AT = "2026-04-20T00:00:00Z"


def solve(task: dict[str, Any], budget: dict[str, Any]) -> dict[str, Any]:
    """Search for a low-degree PSLQ relation and emit a CANB submission."""
    started = time.perf_counter()
    cfg = _normalize_budget(budget)
    target = target_from_spec(task["target_spec"], cfg["dps"])
    best = _search_pslq(target, cfg)
    if best is None:
        best = _fallback_rational(target, cfg["fallback_height"])

    expr, source, num_evaluations = best
    clear_cache()
    value = evaluate(expr, 80)
    target80 = target_from_spec(task["target_spec"], 80)
    if value is None:
        error_text = "inf"
    else:
        error_text = mpmath.nstr(abs(value - target80), 12)

    submission = {
        "task_id": task["id"],
        "method": "pslq",
        "submitted_at": SUBMITTED_AT,
        "status": "success",
        "budget": _budget_payload(budget),
        "metrics": {
            "walltime_sec": float(time.perf_counter() - started),
            "peak_memory_mb": 0.0,
            "num_evaluations": num_evaluations,
        },
        "expression": {
            "format": "aeas-ast-v1",
            "ast": expr_to_ast(expr),
        },
        "error_selfreport_dps80": error_text,
        "notes": source,
    }
    validate_instance(submission, "submission.schema.json")
    return submission


def _normalize_budget(budget: dict[str, Any]) -> dict[str, int]:
    maxcoeff = int(
        budget.get("maxcoeff", budget.get("max_coeff", budget.get("H_max", 200)))
    )
    max_radicand = int(budget.get("max_radicand", 30))
    maxsteps = int(budget.get("maxsteps", budget.get("max_steps", 100)))
    dps = int(budget.get("dps", 120))
    fallback_height = int(budget.get("fallback_height", maxcoeff))
    return {
        "maxcoeff": max(1, maxcoeff),
        "max_radicand": max(1, max_radicand),
        "maxsteps": max(1, maxsteps),
        "dps": max(50, dps),
        "fallback_height": max(1, fallback_height),
    }


def _search_pslq(
    target: mpmath.mpf,
    cfg: dict[str, int],
) -> tuple[ExprNode, str, int] | None:
    squarefree = _squarefree_radicands(cfg["max_radicand"])
    candidates: list[tuple[mpmath.mpf, int, str, ExprNode, int, str]] = []
    evaluations = 0

    def add_candidate(expr: ExprNode, source: str) -> None:
        nonlocal evaluations
        expr = canonicalize(expr)
        clear_cache()
        value = evaluate(expr, cfg["dps"])
        evaluations += 1
        if value is None:
            return
        err = abs(value - target)
        candidates.append(
            (err, expr.node_count, expr.to_str(), expr, evaluations, source)
        )

    relation = _pslq_relation([mpmath.mpf(1), target], cfg)
    if relation is not None and relation[-1] != 0:
        add_candidate(
            _linear_combination([_const(Fraction(1))], relation),
            "PSLQ rational relation",
        )

    for m in squarefree:
        root_m = mpmath.sqrt(m)
        relation = _pslq_relation([mpmath.mpf(1), root_m, target], cfg)
        if relation is not None and relation[-1] != 0:
            add_candidate(
                _linear_combination([_const(Fraction(1)), _sqrt_int(m)], relation),
                f"PSLQ quadratic relation over sqrt({m})",
            )

    for idx, m in enumerate(squarefree):
        root_m = mpmath.sqrt(m)
        for n in squarefree[idx + 1 :]:
            root_n = mpmath.sqrt(n)
            root_mn = mpmath.sqrt(m * n)
            relation = _pslq_relation(
                [mpmath.mpf(1), root_m, root_n, root_mn, target],
                cfg,
            )
            if relation is not None and relation[-1] != 0:
                add_candidate(
                    _linear_combination(
                        [
                            _const(Fraction(1)),
                            _sqrt_int(m),
                            _sqrt_int(n),
                            _sqrt_int(m * n),
                        ],
                        relation,
                    ),
                    f"PSLQ biquadratic relation over sqrt({m}),sqrt({n})",
                )

    if not candidates:
        return None

    _, _, _, expr, relation_evals, source = min(candidates, key=lambda item: item[:3])
    return expr, f"relation_found=true; {source}", relation_evals


def _pslq_relation(values: list[mpmath.mpf], cfg: dict[str, int]) -> list[int] | None:
    with mpmath.workdps(cfg["dps"]):
        relation = mpmath.pslq(
            values,
            maxcoeff=cfg["maxcoeff"],
            maxsteps=cfg["maxsteps"],
        )
    if relation is None:
        return None
    return [int(coef) for coef in relation]


def _linear_combination(bases: list[ExprNode], relation: list[int]) -> ExprNode:
    x_coef = relation[-1]
    if x_coef == 0:
        raise ValueError(f"PSLQ relation has zero target coefficient: {relation!r}")
    terms = []
    for coef, base in zip(relation[:-1], bases):
        scale = Fraction(-coef, x_coef)
        if scale:
            terms.append(_scale(base, scale))
    if not terms:
        return _const(Fraction(0))
    expr = terms[0]
    for term in terms[1:]:
        expr = ExprNode(Op.ADD, children=(expr, term))
    return canonicalize(expr)


def _fallback_rational(
    target: mpmath.mpf,
    max_denominator: int,
) -> tuple[ExprNode, str, int]:
    text = mpmath.nstr(target, 250, strip_zeros=False)
    rational = Fraction(text).limit_denominator(max_denominator)
    return (
        _const(rational),
        "relation_found=false; "
        f"rational fallback denominator <= {max_denominator}",
        1,
    )


def _squarefree_radicands(max_radicand: int) -> list[int]:
    return [n for n in range(2, max_radicand + 1) if _is_squarefree(n)]


def _is_squarefree(n: int) -> bool:
    limit = int(math.isqrt(n))
    for factor in range(2, limit + 1):
        if n % (factor * factor) == 0:
            return False
    return True


def _const(value: Fraction | int) -> ExprNode:
    return ExprNode(Op.CONST, value=Fraction(value))


def _sqrt_int(radicand: int) -> ExprNode:
    return ExprNode(Op.SQRT, children=(_const(radicand),))


def _scale(base: ExprNode, scale: Fraction) -> ExprNode:
    if base.op == Op.CONST and base.value is not None:
        return _const(base.value * scale)
    if scale == 1:
        return base
    return ExprNode(Op.MUL, children=(_const(scale), base))


def _budget_payload(budget: dict[str, Any]) -> dict[str, Any]:
    return {
        "max_walltime_sec": float(
            budget.get("walltime_sec", budget.get("max_walltime_sec", 60))
        ),
        "max_memory_mb": float(
            budget.get("memory_mb", budget.get("max_memory_mb", 2048))
        ),
        "max_evaluations": budget.get("max_evaluations"),
    }
