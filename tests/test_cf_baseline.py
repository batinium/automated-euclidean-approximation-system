from __future__ import annotations

from fractions import Fraction
from typing import Any

from aeas.baselines.cf import solve
from aeas.canb_targets import decimal_truncate, target_from_spec
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
        "difficulty_tier": 1,
        "notes": "synthetic cf test task",
    }


def test_cf_solves_half_exactly() -> None:
    task = _task(
        "canb-algdeg-half",
        "canb-algdeg",
        {
            "kind": "root_of_polynomial",
            "coefficients": [2, -1],
            "real_root_index": 0,
        },
    )
    submission = solve(task, {"walltime_sec": 1, "memory_mb": 512, "H_max": 10})

    validate_instance(submission, "submission.schema.json")
    assert submission["expression"]["ast"] == {"op": "CONST", "value": "1/2"}


def test_cf_respects_denominator_cap() -> None:
    task = _task(
        "canb-transcend-pi",
        "canb-transcend",
        {"kind": "literal_transcendental", "name": "pi"},
    )
    submission = solve(task, {"walltime_sec": 1, "memory_mb": 512, "H_max": 10})
    value = submission["expression"]["ast"]["value"]
    rational = Fraction(value)

    validate_instance(submission, "submission.schema.json")
    assert rational.denominator <= 10
