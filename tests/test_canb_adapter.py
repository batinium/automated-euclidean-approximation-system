from __future__ import annotations

import math
from typing import Any

import pytest

from aeas.ast_io import ast_to_expr
from aeas.canb_adapter import _normalize_budget, solve
from aeas.canb_targets import decimal_truncate, target_from_spec
from aeas.evaluate import evaluate
from aeas.schema_validation import validate_instance


def _task(task_id: str, family: str, target_spec: dict[str, Any]) -> dict[str, Any]:
    value = target_from_spec(target_spec, 120)
    return {
        "id": task_id,
        "family": family,
        "target_description": task_id,
        "target_spec": target_spec,
        "reference_value_dps": 1000,
        "reference_value": decimal_truncate(value, 1000),
        "known_closed_form": None,
        "difficulty_tier": 2,
        "notes": "synthetic adapter test task",
    }


@pytest.mark.parametrize(
    "task",
    [
        _task(
            "canb-transcend-pi",
            "canb-transcend",
            {"kind": "literal_transcendental", "name": "pi"},
        ),
        _task(
            "canb-poly-n7",
            "canb-poly",
            {"kind": "cos_of_rational_pi", "arg": [2, 7]},
        ),
        _task(
            "canb-algdeg-half",
            "canb-algdeg",
            {
                "kind": "root_of_polynomial",
                "coefficients": [2, -1],
                "real_root_index": 0,
            },
        ),
    ],
)
def test_aeas_adapter_returns_valid_finite_submission(task: dict[str, Any]) -> None:
    submission = solve(
        task,
        {
            "walltime_sec": 5,
            "memory_mb": 512,
            "max_evaluations": None,
            "max_depth": 1,
            "max_height": 8,
            "max_radicand": 10,
            "beam_width": 120,
        },
    )

    validate_instance(submission, "submission.schema.json")
    assert submission["status"] == "success"
    assert submission["expression"] is not None
    expr = ast_to_expr(submission["expression"]["ast"])
    value = evaluate(expr, 80)
    assert value is not None
    target = target_from_spec(task["target_spec"], 80)
    assert math.isfinite(float(abs(value - target)))


@pytest.mark.parametrize("q_height_cap", [4, 6])
def test_aeas_adapter_accepts_q_height_cap(q_height_cap: int) -> None:
    task = _task(
        "canb-algdeg-half",
        "canb-algdeg",
        {
            "kind": "root_of_polynomial",
            "coefficients": [2, -1],
            "real_root_index": 0,
        },
    )
    budget = {
        "walltime_sec": 5,
        "memory_mb": 2048,
        "max_evaluations": None,
        "max_depth": 2,
        "max_height": 8,
        "max_radicand": 6,
        "beam_width": 80,
        "aeas_q_height_cap": q_height_cap,
    }
    cfg = _normalize_budget(budget)
    submission = solve(task, budget)

    validate_instance(submission, "submission.schema.json")
    assert cfg.max_height == q_height_cap
    assert submission["status"] == "success"
    assert f"aeas_q_height_cap={q_height_cap}" in submission["notes"]
