from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from aeas.canb_targets import decimal_truncate, target_from_spec
from aeas.schema_validation import validate_instance


ROOT = Path(__file__).resolve().parents[1]


def test_runner_smoke_aeas_transcend(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    subs_dir = tmp_path / "submissions"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_benchmark.py"),
            "--version",
            "0.1",
            "--seed",
            "20260420",
            "--split",
            "canb-transcend",
            "--out",
            str(tasks_dir),
            "--deterministic",
        ],
        check=True,
        cwd=ROOT,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_benchmark.py"),
            "--method",
            "aeas",
            "--split",
            "canb-transcend",
            "--tasks-dir",
            str(tasks_dir),
            "--out",
            str(subs_dir),
            "--budget",
            json.dumps(
                {
                    "walltime_sec": 5,
                    "memory_mb": 512,
                    "max_evaluations": None,
                    "max_depth": 1,
                    "max_height": 6,
                    "max_radicand": 8,
                    "beam_width": 80,
                }
            ),
        ],
        check=True,
        cwd=ROOT,
    )

    submissions = sorted(subs_dir.glob("*.json"))
    assert len(submissions) == 5
    for path in submissions:
        submission = json.loads(path.read_text())
        validate_instance(submission, "submission.schema.json")
        assert submission["method"] == "aeas"


def test_runner_forwards_aeas_q_height_cap(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks" / "canb-algdeg"
    subs_dir = tmp_path / "submissions"
    tasks_dir.mkdir(parents=True)
    target_spec = {
        "kind": "root_of_polynomial",
        "coefficients": [2, -1],
        "real_root_index": 0,
    }
    value = target_from_spec(target_spec, 120)
    task = {
        "id": "canb-algdeg-half",
        "family": "canb-algdeg",
        "target_description": "canb-algdeg-half",
        "target_spec": target_spec,
        "reference_value_dps": 1000,
        "reference_value": decimal_truncate(value, 1000),
        "known_closed_form": None,
        "difficulty_tier": 1,
        "notes": "synthetic runner q-height test",
    }
    (tasks_dir / "canb-algdeg-half.json").write_text(
        json.dumps(task, indent=2, sort_keys=True) + "\n"
    )

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_benchmark.py"),
            "--method",
            "aeas",
            "--split",
            "canb-algdeg",
            "--tasks-dir",
            str(tmp_path / "tasks"),
            "--out",
            str(subs_dir),
            "--budget",
            json.dumps(
                {
                    "walltime_sec": 5,
                    "memory_mb": 2048,
                    "max_evaluations": None,
                    "max_depth": 2,
                    "max_height": 8,
                    "max_radicand": 6,
                    "beam_width": 80,
                }
            ),
            "--aeas-q-height-cap",
            "4",
        ],
        check=True,
        cwd=ROOT,
    )

    submission = json.loads((subs_dir / "canb-algdeg-half.json").read_text())
    validate_instance(submission, "submission.schema.json")
    assert submission["method"] == "aeas"
    assert "aeas_q_height_cap=4" in submission["notes"]
