#!/usr/bin/env python
"""Score CANB submissions against generated tasks."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import mpmath

_root = Path(__file__).resolve().parent.parent
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from aeas.schema_validation import validate_instance  # noqa: E402
from aeas.scoring import ScoredSubmission, score_submission, summary_metrics  # noqa: E402


FIELDNAMES = [
    "row_type",
    "task_id",
    "family",
    "method",
    "status",
    "error",
    "log10_error",
    "node_count",
    "walltime_sec",
    "hypervolume",
    "exact",
    "best_error_median_log10",
    "win_rate_60s",
    "exact_rate",
    "size_at_best_median",
    "expression",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument(
        "--submissions-dir",
        type=Path,
        default=None,
    )
    parser.add_argument("--tasks-dir", type=Path, default=Path("benchmark/tasks"))
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    submissions_dir = args.submissions_dir or (
        Path("benchmark/submissions") / args.method / "0.1"
    )
    out_path = args.out or Path("benchmark/scores") / f"{args.method}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(args.tasks_dir, args.split)
    scores = []
    for task in tasks:
        submission_path = submissions_dir / f"{task['id']}.json"
        submission = None
        if submission_path.exists():
            submission = json.loads(submission_path.read_text())
            validate_instance(submission, "submission.schema.json")
        scores.append(score_submission(task, submission))

    write_scores(out_path, scores, args.method)
    print(f"wrote {out_path}")


def load_tasks(tasks_dir: Path, split: str) -> list[dict[str, Any]]:
    split_dir = tasks_dir / split
    if not split_dir.exists():
        raise FileNotFoundError(f"task split directory not found: {split_dir}")
    tasks = []
    for path in sorted(split_dir.glob("*.json")):
        task = json.loads(path.read_text())
        validate_instance(task, "task.schema.json")
        tasks.append(task)
    if not tasks:
        raise FileNotFoundError(f"no task JSON files found in {split_dir}")
    return tasks


def write_scores(
    out_path: Path,
    scores: list[ScoredSubmission],
    method: str,
) -> None:
    summary = summary_metrics(scores)
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        for score in scores:
            writer.writerow(_score_row(score))
        writer.writerow(
            {
                "row_type": "summary",
                "task_id": "SUMMARY",
                "family": "",
                "method": method,
                "status": "",
                "error": "",
                "log10_error": "",
                "node_count": "",
                "walltime_sec": "",
                "hypervolume": _float_text(summary["score"]),
                "exact": "",
                "best_error_median_log10": _float_text(
                    summary["best_error_median_log10"]
                ),
                "win_rate_60s": _float_text(summary["win_rate_60s"]),
                "exact_rate": _float_text(summary["exact_rate"]),
                "size_at_best_median": _float_text(summary["size_at_best_median"]),
                "expression": "",
            }
        )


def _score_row(score: ScoredSubmission) -> dict[str, Any]:
    return {
        "row_type": "task",
        "task_id": score.task_id,
        "family": score.family,
        "method": score.method,
        "status": score.status,
        "error": "" if score.error is None else mpmath.nstr(score.error, 18),
        "log10_error": "" if score.log10_error is None else _float_text(score.log10_error),
        "node_count": "" if score.node_count is None else score.node_count,
        "walltime_sec": _float_text(score.walltime_sec),
        "hypervolume": _float_text(score.hypervolume),
        "exact": str(score.exact),
        "best_error_median_log10": "",
        "win_rate_60s": "",
        "exact_rate": "",
        "size_at_best_median": "",
        "expression": score.expression,
    }


def _float_text(value: float) -> str:
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return f"{value:.12g}"


if __name__ == "__main__":
    main()
