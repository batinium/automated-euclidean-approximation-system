#!/usr/bin/env python
"""
Automated deep sweep runner for AEAS.

Usage (from repo root, with env already active):

    micromamba activate aeas
    python scripts/auto_deep_sweep.py \
        --n 13 \
        --depths 3 4 5 6 \
        --nodes 25 35 \
        --beams 2000 5000 10000 \
        --output_root results_deepdiag \
        --name_prefix autosweep \
        --progress

This will:
  - Run `scripts/run_search.py` for every (depth, nodes, beam) combination.
  - Write each run under <output_root>/<run_name>/.
  - Merge all `summary.csv` files into
      <output_root>/all_summaries_with_run.csv
    with an extra `run_name` column for later analysis.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SEARCH_SCRIPT = ROOT / "scripts" / "run_search.py"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Automated deep sweep driver for AEAS beam_search.",
    )
    ap.add_argument(
        "--n",
        type=int,
        nargs="+",
        default=[13],
        help="Values of n to approximate cos(2π/n) for (default: 13).",
    )
    ap.add_argument(
        "--depths",
        type=int,
        nargs="+",
        default=[3, 4, 5, 6],
        help="List of max_depth values to sweep.",
    )
    ap.add_argument(
        "--nodes",
        type=int,
        nargs="+",
        default=[25, 35],
        help="List of max_nodes values to sweep.",
    )
    ap.add_argument(
        "--beams",
        type=int,
        nargs="+",
        default=[2000, 5000, 10000],
        help="List of beam_width values to sweep.",
    )
    ap.add_argument(
        "--dps",
        type=int,
        default=80,
        help="Decimal precision to use (passed through to run_search).",
    )
    ap.add_argument(
        "--output_root",
        type=str,
        default="results_deepdiag",
        help="Root directory for saving run outputs.",
    )
    ap.add_argument(
        "--name_prefix",
        type=str,
        default="autosweep",
        help="Prefix for run_name (suffix encodes parameters).",
    )
    ap.add_argument(
        "--const_set",
        type=str,
        default="0,1,-1,1/2,2,3/2,3,1/4,1/3,2/3,3/4,4/3,5/4",
        help="Comma-separated rational constants for the search.",
    )
    ap.add_argument(
        "--progress",
        action="store_true",
        help="Pass --progress through to run_search for per-depth logs.",
    )
    return ap.parse_args()


def build_run_name(
    prefix: str,
    n_vals: list[int],
    depth: int,
    nodes: int,
    beam: int,
) -> str:
    n_part = "-".join(str(n) for n in n_vals)
    return f"{prefix}_n{n_part}_d{depth}_nodes{nodes}_beam{beam}"


def run_one(
    n_vals: list[int],
    depth: int,
    nodes: int,
    beam: int,
    dps: int,
    const_set: str,
    output_root: Path,
    name_prefix: str,
    progress: bool,
) -> tuple[str, float, bool]:
    run_name = build_run_name(name_prefix, n_vals, depth, nodes, beam)
    run_dir = output_root / run_name

    summary_path = run_dir / "summary.csv"
    if summary_path.exists():
        print(f"[SKIP] {run_name} (summary.csv already exists)")
        return run_name, 0.0, True

    cmd = [
        sys.executable,
        str(SEARCH_SCRIPT),
        "--n",
        *[str(n) for n in n_vals],
        "--max_depth",
        str(depth),
        "--max_nodes",
        str(nodes),
        "--beam_width",
        str(beam),
        "--dps",
        str(dps),
        "--const_set",
        const_set,
        "--output_root",
        str(output_root),
        "--run_name",
        run_name,
    ]
    if progress:
        cmd.append("--progress")

    print("\n" + "=" * 70)
    print(f"RUNNING: {run_name}")
    print("CMD: " + " ".join(cmd))
    print("=" * 70)

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,
        )
        elapsed = time.time() - t0
        if proc.returncode != 0:
            print(f"[FAIL] {run_name} after {elapsed:.1f}s")
            print(proc.stderr[:800])
            return run_name, elapsed, False
        print(f"[OK]   {run_name} in {elapsed:.1f}s")
        return run_name, elapsed, True
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        print(f"[TIMEOUT] {run_name} after {elapsed:.1f}s")
        return run_name, elapsed, False


def consolidate(output_root: Path) -> Path:
    combined = []
    for sub in sorted(output_root.iterdir()):
        if not sub.is_dir():
            continue
        summary = sub / "summary.csv"
        if not summary.exists():
            continue
        with summary.open() as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                row["run_name"] = sub.name
                combined.append(row)

    out_path = output_root / "all_summaries_with_run.csv"
    if not combined:
        print("No summary.csv files found to consolidate.")
        return out_path

    fieldnames = ["run_name"] + [k for k in combined[0] if k != "run_name"]
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in combined:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    print(
        f"\nConsolidated {len(combined)} rows into "
        f"{out_path.relative_to(output_root.parent)}"
    )
    return out_path


def main() -> None:
    args = parse_args()
    output_root = ROOT / args.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    print("AEAS automated deep sweep")
    print(f"  root       : {ROOT}")
    print(f"  output_root: {output_root}")
    print(f"  n          : {args.n}")
    print(f"  depths     : {args.depths}")
    print(f"  nodes      : {args.nodes}")
    print(f"  beams      : {args.beams}")
    print()

    results: list[tuple[str, float, bool]] = []
    total = len(args.depths) * len(args.nodes) * len(args.beams)
    idx = 0

    for depth in args.depths:
        for nodes in args.nodes:
            for beam in args.beams:
                idx += 1
                print(f"\n[{idx}/{total}] depth={depth} nodes={nodes} beam={beam}")
                results.append(
                    run_one(
                        n_vals=args.n,
                        depth=depth,
                        nodes=nodes,
                        beam=beam,
                        dps=args.dps,
                        const_set=args.const_set,
                        output_root=output_root,
                        name_prefix=args.name_prefix,
                        progress=args.progress,
                    )
                )

    print("\n" + "=" * 70)
    print("CONSOLIDATING")
    print("=" * 70)
    consolidate(output_root)

    print("\nRun summary:")
    for rn, elapsed, ok in results:
        status = "OK" if ok else "FAIL"
        print(f"  {status:4s}  {elapsed:7.1f}s  {rn}")


if __name__ == "__main__":
    main()

