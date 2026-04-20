from __future__ import annotations

import filecmp
import subprocess
import sys
from pathlib import Path

from aeas.schema_validation import validate_instance


ROOT = Path(__file__).resolve().parents[1]


def _collect_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def _assert_dirs_equal(left: Path, right: Path) -> None:
    left_files = [path.relative_to(left) for path in _collect_files(left)]
    right_files = [path.relative_to(right) for path in _collect_files(right)]
    assert left_files == right_files
    for rel in left_files:
        assert filecmp.cmp(left / rel, right / rel, shallow=False), rel


def test_generator_is_byte_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "generate_benchmark.py"),
        "--version",
        "0.1",
        "--seed",
        "20260420",
        "--split",
        "all",
        "--deterministic",
    ]

    subprocess.run([*cmd, "--out", str(first / "tasks")], check=True, cwd=ROOT)
    subprocess.run([*cmd, "--out", str(second / "tasks")], check=True, cwd=ROOT)

    _assert_dirs_equal(first, second)


def test_generator_outputs_valid_transcend_tasks(tmp_path: Path) -> None:
    out = tmp_path / "tasks"
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
            str(out),
            "--deterministic",
        ],
        check=True,
        cwd=ROOT,
    )

    task_paths = sorted((out / "canb-transcend").glob("*.json"))
    assert len(task_paths) == 5
    for path in task_paths:
        validate_instance(__import__("json").loads(path.read_text()), "task.schema.json")
