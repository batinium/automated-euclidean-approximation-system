#!/usr/bin/env python
"""Summarize CANB score CSVs into a compact method comparison table."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from statistics import median
from typing import Any


FIELDNAMES = [
    "split",
    "method",
    "tasks",
    "successes",
    "median_error",
    "median_log10_error",
    "median_nodes",
    "median_walltime_sec",
    "total_walltime_sec",
    "exact_rate",
    "Cpath",
    "source_path",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--score",
        action="append",
        default=[],
        metavar="METHOD=CSV",
        help="Explicit score CSV. May be repeated. If omitted, discover scores.",
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Print a markdown table to stdout after writing CSV output.",
    )
    args = parser.parse_args()

    score_paths = parse_score_args(args.score)
    if not score_paths:
        score_paths = discover_score_paths(args.root, args.split)
    if not score_paths:
        raise SystemExit(f"no score CSVs found for split {args.split!r}")

    summaries = [
        summarize_score(path=path, method=method, split=args.split)
        for method, path in sorted(score_paths.items())
    ]

    if args.out is None:
        write_csv(sys.stdout, summaries)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", newline="") as fh:
            write_csv(fh, summaries)

    if args.markdown:
        print(markdown_table(summaries))


def parse_score_args(values: list[str]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"--score must be METHOD=CSV, got {value!r}")
        method, raw_path = value.split("=", 1)
        method = method.strip()
        if not method:
            raise SystemExit(f"--score has empty method in {value!r}")
        paths[method] = Path(raw_path)
    return paths


def discover_score_paths(root: Path, split: str) -> dict[str, Path]:
    candidates = [
        *(root / "benchmark" / "runs").glob("*/score.csv"),
        *(root / "benchmark" / "scores").glob("*.csv"),
    ]
    discovered: dict[str, Path] = {}
    for path in sorted(candidates):
        if not path.exists():
            continue
        try:
            score_split, method = score_identity(path)
        except ValueError:
            continue
        if score_split != split:
            continue
        previous = discovered.get(method)
        if previous is None or path.stat().st_mtime > previous.stat().st_mtime:
            discovered[method] = path
    return discovered


def score_identity(path: Path) -> tuple[str, str]:
    task_rows, summary = read_score(path)
    families = {row["family"] for row in task_rows if row.get("family")}
    methods = {row["method"] for row in task_rows if row.get("method")}
    if not task_rows or len(families) != 1 or len(methods) != 1:
        raise ValueError(f"cannot infer score identity from {path}")
    method = summary.get("method") or next(iter(methods))
    return next(iter(families)), method


def summarize_score(path: Path, method: str, split: str) -> dict[str, str]:
    task_rows, summary = read_score(path)
    split_rows = [row for row in task_rows if row.get("family") == split]
    if not split_rows:
        raise ValueError(f"{path} has no task rows for split {split!r}")

    success_rows = [row for row in split_rows if row.get("status") == "success"]
    errors = [_float(row["error"]) for row in success_rows if row.get("error")]
    logs = [_float(row["log10_error"]) for row in success_rows if row.get("log10_error")]
    nodes = [_float(row["node_count"]) for row in success_rows if row.get("node_count")]
    times = [
        _float(row["walltime_sec"])
        for row in success_rows
        if row.get("walltime_sec")
    ]
    exact_count = sum(1 for row in success_rows if row.get("exact") == "True")

    return {
        "split": split,
        "method": method,
        "tasks": str(len(split_rows)),
        "successes": str(len(success_rows)),
        "median_error": _metric_text(median(errors) if errors else math.nan),
        "median_log10_error": _metric_text(median(logs) if logs else math.nan),
        "median_nodes": _metric_text(median(nodes) if nodes else math.nan),
        "median_walltime_sec": _metric_text(median(times) if times else math.nan),
        "total_walltime_sec": _metric_text(sum(times) if times else math.nan),
        "exact_rate": _metric_text(
            exact_count / len(split_rows) if split_rows else math.nan
        ),
        "Cpath": summary.get("hypervolume", ""),
        "source_path": str(path),
    }


def read_score(path: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    task_rows = [row for row in rows if row.get("row_type") == "task"]
    summaries = [row for row in rows if row.get("row_type") == "summary"]
    if not summaries:
        raise ValueError(f"{path} has no summary row")
    return task_rows, summaries[-1]


def write_csv(fh: Any, summaries: list[dict[str, str]]) -> None:
    writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
    writer.writeheader()
    for summary in summaries:
        writer.writerow(summary)


def markdown_table(summaries: list[dict[str, str]]) -> str:
    headers = [
        "method",
        "tasks",
        "median_error",
        "median_nodes",
        "median_walltime_sec",
        "exact_rate",
        "Cpath",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in summaries:
        lines.append("| " + " | ".join(summary[key] for key in headers) + " |")
    return "\n".join(lines)


def _float(text: str) -> float:
    return float(text)


def _metric_text(value: float) -> str:
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return f"{value:.12g}"


if __name__ == "__main__":
    main()
