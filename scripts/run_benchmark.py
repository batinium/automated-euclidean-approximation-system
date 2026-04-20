#!/usr/bin/env python
"""Run a registered CANB method over a task split."""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

_root = Path(__file__).resolve().parent.parent
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from aeas.methods import get_method  # noqa: E402
from aeas.schema_validation import validate_instance  # noqa: E402


DEFAULT_BUDGET = {
    "walltime_sec": 60,
    "memory_mb": 2048,
    "max_evaluations": None,
}
SUBMITTED_AT = "2026-04-20T00:00:00Z"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument("--tasks-dir", type=Path, default=Path("benchmark/tasks"))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--budget", type=str, default=json.dumps(DEFAULT_BUDGET))
    parser.add_argument("--aeas-q-height-cap", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--n-parallel", type=int, default=1)
    args = parser.parse_args()

    budget = json.loads(args.budget)
    if args.aeas_q_height_cap is not None:
        if args.method != "aeas":
            parser.error("--aeas-q-height-cap can only be used with --method aeas")
        budget["aeas_q_height_cap"] = args.aeas_q_height_cap
    out_dir = args.out or Path("benchmark/submissions") / args.method / "0.1"
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(args.tasks_dir, args.split)
    pending = []
    for path, task in tasks:
        target = out_dir / f"{task['id']}.json"
        if args.resume and target.exists():
            continue
        pending.append((path, target))

    if args.n_parallel <= 1:
        for task_path, output_path in pending:
            submission = _run_one(args.method, task_path, budget)
            _write_submission(submission, output_path)
            print(f"wrote {output_path}")
    else:
        with ProcessPoolExecutor(max_workers=args.n_parallel) as pool:
            futures = {
                pool.submit(_run_one, args.method, task_path, budget): output_path
                for task_path, output_path in pending
            }
            for future in as_completed(futures):
                output_path = futures[future]
                submission = future.result()
                _write_submission(submission, output_path)
                print(f"wrote {output_path}")

    print(f"completed {len(pending)} tasks for method={args.method}")


def load_tasks(tasks_dir: Path, split: str) -> list[tuple[Path, dict[str, Any]]]:
    split_dir = tasks_dir / split
    if not split_dir.exists():
        raise FileNotFoundError(f"task split directory not found: {split_dir}")
    tasks = []
    for path in sorted(split_dir.glob("*.json")):
        task = json.loads(path.read_text())
        validate_instance(task, "task.schema.json")
        tasks.append((path, task))
    if not tasks:
        raise FileNotFoundError(f"no task JSON files found in {split_dir}")
    return tasks


def _run_one(
    method_name: str,
    task_path: Path,
    budget: dict[str, Any],
) -> dict[str, Any]:
    task = json.loads(task_path.read_text())
    started = time.perf_counter()
    rss_before = _peak_rss_mb()
    try:
        method = get_method(method_name)
        submission = method(task, budget)
        status_note = submission.get("notes", "")
    except Exception as exc:
        submission = _failed_submission(
            task,
            method_name,
            budget,
            walltime_sec=time.perf_counter() - started,
            notes=f"{type(exc).__name__}: {exc}",
        )
        status_note = submission["notes"]

    elapsed = time.perf_counter() - started
    submission["method"] = method_name
    submission["task_id"] = task["id"]
    submission["submitted_at"] = SUBMITTED_AT
    submission["metrics"]["walltime_sec"] = float(elapsed)
    submission["metrics"]["peak_memory_mb"] = max(_peak_rss_mb(), rss_before)
    if "status" not in submission:
        submission["status"] = "success"
    if not submission.get("notes"):
        submission["notes"] = status_note
    validate_instance(submission, "submission.schema.json")
    return submission


def _write_submission(submission: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(submission, indent=2, sort_keys=True) + "\n")


def _failed_submission(
    task: dict[str, Any],
    method_name: str,
    budget: dict[str, Any],
    walltime_sec: float,
    notes: str,
) -> dict[str, Any]:
    return {
        "task_id": task["id"],
        "method": method_name,
        "submitted_at": SUBMITTED_AT,
        "status": "failed",
        "budget": _budget_payload(budget),
        "metrics": {
            "walltime_sec": float(walltime_sec),
            "peak_memory_mb": 0.0,
            "num_evaluations": 0,
        },
        "expression": None,
        "error_selfreport_dps80": None,
        "notes": notes,
    }


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


def _peak_rss_mb() -> float:
    rss = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return rss / (1024 * 1024)
    return rss / 1024


if __name__ == "__main__":
    main()
