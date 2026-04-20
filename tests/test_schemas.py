from __future__ import annotations

import json
from pathlib import Path

import pytest

from aeas.schema_validation import SchemaValidationError, validate_instance


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "benchmark" / "schema"


def _load_schema(name: str) -> dict:
    with (SCHEMA_DIR / name).open() as fh:
        return json.load(fh)


def test_ast_schema_positive_and_negative() -> None:
    valid = {
        "op": "ADD",
        "args": [
            {"op": "CONST", "value": "1/2"},
            {"op": "SQRT", "args": [{"op": "CONST", "value": "7/1"}]},
        ],
    }
    invalid = {"op": "CONST", "value": "0.5"}

    _load_schema("ast.schema.json")
    validate_instance(valid, "ast.schema.json")
    with pytest.raises(SchemaValidationError):
        validate_instance(invalid, "ast.schema.json")


def test_task_schema_positive_and_negative() -> None:
    valid = {
        "id": "canb-poly-n7",
        "family": "canb-poly",
        "target_description": "cos(2*pi/7)",
        "target_spec": {"kind": "cos_of_rational_pi", "arg": [2, 7]},
        "reference_value_dps": 1000,
        "reference_value": "0.62348980185873353053",
        "known_closed_form": None,
        "difficulty_tier": 2,
        "notes": "non-Gauss-Wantzel heptagon",
    }
    invalid = dict(valid)
    invalid["target_spec"] = {"kind": "literal_transcendental", "name": "tau"}

    _load_schema("task.schema.json")
    validate_instance(valid, "task.schema.json")
    with pytest.raises(SchemaValidationError):
        validate_instance(invalid, "task.schema.json")


def test_submission_schema_positive_and_negative() -> None:
    valid = {
        "task_id": "canb-poly-n7",
        "method": "aeas",
        "submitted_at": "2026-04-20T00:00:00Z",
        "status": "success",
        "budget": {
            "max_walltime_sec": 60,
            "max_memory_mb": 2048,
            "max_evaluations": None,
        },
        "metrics": {
            "walltime_sec": 1.25,
            "peak_memory_mb": 128.0,
            "num_evaluations": 42,
        },
        "expression": {
            "format": "aeas-ast-v1",
            "ast": {"op": "CONST", "value": "1/2"},
        },
        "error_selfreport_dps80": "1e-6",
        "notes": "handcrafted positive example",
    }
    invalid = dict(valid)
    invalid["expression"] = {
        "format": "aeas-ast-v1",
        "ast": {"op": "POW", "args": [{"op": "CONST", "value": "1/2"}]},
    }

    _load_schema("submission.schema.json")
    validate_instance(valid, "submission.schema.json")
    with pytest.raises(SchemaValidationError):
        validate_instance(invalid, "submission.schema.json")
