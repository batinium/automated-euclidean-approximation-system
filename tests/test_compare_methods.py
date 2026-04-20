from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_compare_methods_summarizes_score_csvs(tmp_path: Path) -> None:
    aeas = tmp_path / "aeas.csv"
    cf = tmp_path / "cf.csv"
    _write_score(
        aeas,
        "aeas",
        errors=["1e-8", "3e-8", "5e-8"],
        nodes=["11", "11", "13"],
        times=["1.0", "1.2", "1.4"],
        cpath="0.08",
    )
    _write_score(
        cf,
        "cf",
        errors=["1e-3", "2e-3", "3e-3"],
        nodes=["1", "1", "1"],
        times=["0.001", "0.002", "0.003"],
        cpath="0.11",
    )
    out = tmp_path / "comparison.csv"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "compare_methods.py"),
            "--split",
            "canb-poly",
            "--score",
            f"aeas={aeas}",
            "--score",
            f"cf={cf}",
            "--out",
            str(out),
        ],
        check=True,
        cwd=ROOT,
    )

    rows = {row["method"]: row for row in csv.DictReader(out.open())}
    assert rows["aeas"]["tasks"] == "3"
    assert rows["aeas"]["successes"] == "3"
    assert rows["aeas"]["median_error"] == "3e-08"
    assert rows["aeas"]["median_nodes"] == "11"
    assert rows["cf"]["median_error"] == "0.002"
    assert rows["cf"]["median_walltime_sec"] == "0.002"
    assert rows["cf"]["Cpath"] == "0.11"


def _write_score(
    path: Path,
    method: str,
    errors: list[str],
    nodes: list[str],
    times: list[str],
    cpath: str,
) -> None:
    fieldnames = [
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
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for idx, (error, node_count, walltime) in enumerate(
            zip(errors, nodes, times),
            start=1,
        ):
            writer.writerow(
                {
                    "row_type": "task",
                    "task_id": f"canb-poly-n{idx}",
                    "family": "canb-poly",
                    "method": method,
                    "status": "success",
                    "error": error,
                    "log10_error": "-8",
                    "node_count": node_count,
                    "walltime_sec": walltime,
                    "hypervolume": "0.01",
                    "exact": "False",
                    "expression": "1",
                }
            )
        writer.writerow(
            {
                "row_type": "summary",
                "task_id": "SUMMARY",
                "method": method,
                "hypervolume": cpath,
                "best_error_median_log10": "-8",
                "win_rate_60s": "nan",
                "exact_rate": "0",
                "size_at_best_median": "1",
            }
        )
