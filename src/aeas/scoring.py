"""Scoring utilities for CANB submissions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Any

import mpmath

from .ast_io import ast_to_expr
from .canonicalize import canonicalize
from .evaluate import clear_cache, evaluate


ERROR_LOG_RANGE = (-30.0, 0.0)
SIZE_LOG_RANGE = (0.0, 3.0)
TIME_LOG_RANGE = (-3.0, 3.0)
ERROR_CLAMP = mpmath.mpf("1e-100")


@dataclass(frozen=True)
class ScoredSubmission:
    task_id: str
    family: str
    method: str
    status: str
    error: mpmath.mpf | None
    log10_error: float | None
    node_count: int | None
    walltime_sec: float
    hypervolume: float
    exact: bool
    expression: str


def score_submission(
    task: dict[str, Any],
    submission: dict[str, Any] | None,
) -> ScoredSubmission:
    """Re-evaluate and score one submission against one task."""
    if submission is None or submission.get("expression") is None:
        return _failed_score(task, submission)

    clear_cache()
    expr = canonicalize(ast_to_expr(submission["expression"]["ast"]))
    value = evaluate(expr, 1000)
    if value is None:
        return _failed_score(task, submission)

    with mpmath.workdps(1100):
        target = mpmath.mpf(task["reference_value"])
        error = abs(value - target)
        clamped = max(error, ERROR_CLAMP)
        log10_error = float(mpmath.log10(clamped))

    walltime = float(submission["metrics"].get("walltime_sec", 0.0))
    point = normalized_point(error, expr.node_count, walltime)
    hv = pareto_hypervolume([point])
    return ScoredSubmission(
        task_id=task["id"],
        family=task["family"],
        method=submission.get("method", ""),
        status=submission.get("status", "success"),
        error=error,
        log10_error=log10_error,
        node_count=expr.node_count,
        walltime_sec=walltime,
        hypervolume=hv,
        exact=error < mpmath.mpf("1e-20"),
        expression=expr.to_str(),
    )


def normalized_point(
    error: mpmath.mpf,
    node_count: int,
    walltime_sec: float,
) -> tuple[float, float, float]:
    clamped_error = max(error, ERROR_CLAMP)
    log_error = float(mpmath.log10(clamped_error))
    log_size = math.log10(max(float(node_count), 1.0))
    log_time = math.log10(max(float(walltime_sec), 1e-3))
    return (
        _invert_box(log_error, *ERROR_LOG_RANGE),
        _invert_box(log_size, *SIZE_LOG_RANGE),
        _invert_box(log_time, *TIME_LOG_RANGE),
    )


def pareto_hypervolume(points: list[tuple[float, float, float]]) -> float:
    """Exact dominated hypervolume in [0, 1]^3 relative to the origin."""
    filtered = [
        (max(0.0, min(1.0, x)), max(0.0, min(1.0, y)), max(0.0, min(1.0, z)))
        for x, y, z in points
        if x > 0 and y > 0 and z > 0
    ]
    if not filtered:
        return 0.0
    xs = sorted({0.0, *(x for x, _, _ in filtered)})
    volume = 0.0
    for left, right in zip(xs, xs[1:]):
        active = [(y, z) for x, y, z in filtered if x >= right]
        if active:
            volume += (right - left) * _area_2d(active)
    return volume


def summary_metrics(scores: list[ScoredSubmission]) -> dict[str, float]:
    valid = [score for score in scores if score.error is not None]
    if not valid:
        return {
            "score": 0.0,
            "best_error_median_log10": math.nan,
            "win_rate_60s": math.nan,
            "exact_rate": 0.0,
            "size_at_best_median": math.nan,
        }
    return {
        "score": sum(score.hypervolume for score in scores) / len(scores),
        "best_error_median_log10": float(
            median(score.log10_error for score in valid if score.log10_error is not None)
        ),
        "win_rate_60s": math.nan,
        "exact_rate": sum(1 for score in valid if score.exact) / len(scores),
        "size_at_best_median": float(
            median(score.node_count for score in valid if score.node_count is not None)
        ),
    }


def _failed_score(
    task: dict[str, Any],
    submission: dict[str, Any] | None,
) -> ScoredSubmission:
    method = "" if submission is None else submission.get("method", "")
    status = "missing" if submission is None else submission.get("status", "failed")
    walltime = (
        0.0
        if submission is None
        else float(submission.get("metrics", {}).get("walltime_sec", 0.0))
    )
    return ScoredSubmission(
        task_id=task["id"],
        family=task["family"],
        method=method,
        status=status,
        error=None,
        log10_error=None,
        node_count=None,
        walltime_sec=walltime,
        hypervolume=0.0,
        exact=False,
        expression="",
    )


def _invert_box(value: float, lo: float, hi: float) -> float:
    clamped = min(max(value, lo), hi)
    return (hi - clamped) / (hi - lo)


def _area_2d(points: list[tuple[float, float]]) -> float:
    ys = sorted({0.0, *(y for y, _ in points)})
    area = 0.0
    for bottom, top in zip(ys, ys[1:]):
        active_z = [z for y, z in points if y >= top]
        if active_z:
            area += (top - bottom) * max(active_z)
    return area
