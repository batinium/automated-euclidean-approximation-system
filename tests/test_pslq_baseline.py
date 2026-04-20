from __future__ import annotations

import math
from typing import Any

from aeas.ast_io import ast_to_expr
from aeas.baselines.pslq import solve
from aeas.canb_targets import decimal_truncate, target_from_spec
from aeas.evaluate import evaluate
from aeas.methods import get_method
from aeas.schema_validation import validate_instance
from aeas.scoring import score_submission


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
        "difficulty_tier": 1,
        "notes": "synthetic pslq test task",
    }


def test_pslq_registry_hit() -> None:
    assert get_method("pslq") is solve


def test_pslq_deterministic_single_task_run() -> None:
    task = _task(
        "canb-algdeg-half",
        "canb-algdeg",
        {
            "kind": "root_of_polynomial",
            "coefficients": [2, -1],
            "real_root_index": 0,
        },
    )
    budget = {"walltime_sec": 1, "memory_mb": 512, "maxcoeff": 20}

    first = solve(task, budget)
    second = solve(task, budget)

    validate_instance(first, "submission.schema.json")
    validate_instance(second, "submission.schema.json")
    assert first["status"] == "success"
    assert first["expression"]["ast"] == second["expression"]["ast"]
    assert first["expression"]["ast"] == {"op": "CONST", "value": "1/2"}
    assert first["notes"].startswith("relation_found=true;")


def test_pslq_valid_schema_and_finite_score() -> None:
    task = _task(
        "canb-transcend-pi",
        "canb-transcend",
        {"kind": "literal_transcendental", "name": "pi"},
    )
    submission = solve(
        task,
        {
            "walltime_sec": 1,
            "memory_mb": 512,
            "maxcoeff": 20,
            "max_radicand": 6,
            "fallback_height": 20,
        },
    )

    validate_instance(submission, "submission.schema.json")
    expr = ast_to_expr(submission["expression"]["ast"])
    value = evaluate(expr, 80)
    target = target_from_spec(task["target_spec"], 80)
    score = score_submission(task, submission)

    assert value is not None
    assert math.isfinite(float(abs(value - target)))
    assert score.error is not None
    assert math.isfinite(float(score.log10_error))
    assert score.hypervolume > 0
    assert submission["notes"].startswith("relation_found=false;")
