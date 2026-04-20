from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from aeas.canb_targets import decimal_truncate, target_from_spec


ROOT = Path(__file__).resolve().parents[1]


def test_scorer_hypervolume_is_error_monotone(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks" / "canb-algdeg"
    subs_dir = tmp_path / "subs"
    tasks_dir.mkdir(parents=True)
    subs_dir.mkdir()
    specs = [
        ("canb-algdeg-exact", "1/2"),
        ("canb-algdeg-near", "1/3"),
        ("canb-algdeg-far", "1/1"),
    ]
    target_spec = {
        "kind": "root_of_polynomial",
        "coefficients": [2, -1],
        "real_root_index": 0,
    }
    value = target_from_spec(target_spec, 120)
    for task_id, rational in specs:
        task = {
            "id": task_id,
            "family": "canb-algdeg",
            "target_description": task_id,
            "target_spec": target_spec,
            "reference_value_dps": 1000,
            "reference_value": decimal_truncate(value, 1000),
            "known_closed_form": None,
            "difficulty_tier": 1,
            "notes": "synthetic scorer test",
        }
        (tasks_dir / f"{task_id}.json").write_text(
            json.dumps(task, indent=2, sort_keys=True) + "\n"
        )
        submission = {
            "task_id": task_id,
            "method": "toy",
            "submitted_at": "2026-04-20T00:00:00Z",
            "status": "success",
            "budget": {
                "max_walltime_sec": 60,
                "max_memory_mb": 2048,
                "max_evaluations": None,
            },
            "metrics": {
                "walltime_sec": 1.0,
                "peak_memory_mb": 1.0,
                "num_evaluations": 1,
            },
            "expression": {
                "format": "aeas-ast-v1",
                "ast": {"op": "CONST", "value": rational},
            },
            "error_selfreport_dps80": "0",
            "notes": "synthetic",
        }
        (subs_dir / f"{task_id}.json").write_text(
            json.dumps(submission, indent=2, sort_keys=True) + "\n"
        )

    out = tmp_path / "scores.csv"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "score_benchmark.py"),
            "--method",
            "toy",
            "--split",
            "canb-algdeg",
            "--tasks-dir",
            str(tmp_path / "tasks"),
            "--submissions-dir",
            str(subs_dir),
            "--out",
            str(out),
        ],
        check=True,
        cwd=ROOT,
    )

    rows = {
        row["task_id"]: row
        for row in csv.DictReader(out.open())
        if row["row_type"] == "task"
    }
    exact = float(rows["canb-algdeg-exact"]["hypervolume"])
    near = float(rows["canb-algdeg-near"]["hypervolume"])
    far = float(rows["canb-algdeg-far"]["hypervolume"])
    assert exact > near > far

    summary = [
        row for row in csv.DictReader(out.open()) if row["row_type"] == "summary"
    ][0]
    assert summary["win_rate_60s"] == "nan"
