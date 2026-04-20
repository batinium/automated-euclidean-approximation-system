"""Continued-fractions baseline for CANB."""

from __future__ import annotations

import time
from fractions import Fraction
from typing import Any

import mpmath

from aeas.canb_targets import target_from_spec
from aeas.schema_validation import validate_instance


SUBMITTED_AT = "2026-04-20T00:00:00Z"


def solve(task: dict[str, Any], budget: dict[str, Any]) -> dict[str, Any]:
    """Return the best rational p/q with q <= H_max."""
    started = time.perf_counter()
    h_max = int(
        budget.get("H_max", budget.get("max_denom", budget.get("max_height", 200)))
    )
    h_max = max(h_max, 1)
    target = target_from_spec(task["target_spec"], 200)
    approx = _best_rational(target, h_max)
    error = abs(
        mpmath.mpf(approx.numerator) / mpmath.mpf(approx.denominator)
        - target_from_spec(task["target_spec"], 80)
    )
    submission = {
        "task_id": task["id"],
        "method": "cf",
        "submitted_at": SUBMITTED_AT,
        "status": "success",
        "budget": _budget_payload(budget),
        "metrics": {
            "walltime_sec": float(time.perf_counter() - started),
            "peak_memory_mb": 0.0,
            "num_evaluations": 1,
        },
        "expression": {
            "format": "aeas-ast-v1",
            "ast": {
                "op": "CONST",
                "value": f"{approx.numerator}/{approx.denominator}",
            },
        },
        "error_selfreport_dps80": mpmath.nstr(error, 12),
        "notes": f"continued fractions with denominator <= {h_max}",
    }
    validate_instance(submission, "submission.schema.json")
    return submission


def _best_rational(target: mpmath.mpf, max_denominator: int) -> Fraction:
    text = mpmath.nstr(target, 250, strip_zeros=False)
    return Fraction(text).limit_denominator(max_denominator)


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
