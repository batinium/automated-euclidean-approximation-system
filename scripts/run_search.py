#!/usr/bin/env python
"""CLI entry-point for the Automated Euclidean Approximation System."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

from rich.console import Console
from rich.table import Table

_root = Path(__file__).resolve().parent.parent
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from aeas.evaluate import compute_target  # noqa: E402
from aeas.search import beam_search, baseline_enumerate  # noqa: E402
from aeas.field_search import field_search  # noqa: E402


def _parse_const_set(raw: str) -> list[Fraction]:
    return [Fraction(x.strip()) for x in raw.split(",")]


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Search for constructible-number approximations to cos(2π/n).",
    )
    ap.add_argument(
        "--n", type=int, nargs="+", default=[7, 11, 13],
        help="Values of n to approximate cos(2π/n) for",
    )
    ap.add_argument("--max_depth", type=int, default=3)
    ap.add_argument("--max_nodes", type=int, default=15)
    ap.add_argument("--beam_width", type=int, default=2000)
    ap.add_argument("--dps", type=int, default=80)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--mode", choices=["beam", "baseline", "field"], default="beam")
    ap.add_argument(
        "--const_set",
        type=str,
        default="0,1,-1,1/2,2,3/2,3,1/4,1/3",
        help="Comma-separated rational constants (beam/baseline modes)",
    )
    ap.add_argument(
        "--max_height",
        type=int,
        default=20,
        help="Max numerator/denominator for rational coefficients (field mode)",
    )
    ap.add_argument(
        "--max_radicand",
        type=int,
        default=30,
        help="Largest squarefree radicand to search (field mode)",
    )
    ap.add_argument(
        "--output_root",
        type=str,
        default="results",
        help="Root directory for saving run outputs (one subdir per run).",
    )
    ap.add_argument(
        "--run_name",
        type=str,
        default=None,
        help="Optional name for this run (subdirectory under output_root). "
        "If omitted, a timestamped name based on key parameters is used.",
    )
    ap.add_argument("--top_k", type=int, default=10)
    ap.add_argument(
        "--progress",
        action="store_true",
        help="Print per-depth beam_search progress (useful for long runs).",
    )
    args = ap.parse_args()

    const_set = _parse_const_set(args.const_set)
    console = Console()

    # ── determine run directory ──
    from datetime import datetime
    import json as _json

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    if args.run_name:
        run_name = args.run_name
    else:
        n_part = "-".join(str(n) for n in args.n)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_name = (
            f"n{n_part}_d{args.max_depth}_nodes{args.max_nodes}_"
            f"beam{args.beam_width}_{ts}"
        )

    results_dir = output_root / run_name
    results_dir.mkdir(parents=True, exist_ok=True)

    # Persist run configuration so experiments are easily reproducible.
    meta = {
        "run_name": run_name,
        "output_root": str(output_root),
        "results_dir": str(results_dir),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "args": {
            "n": list(args.n),
            "max_depth": args.max_depth,
            "max_nodes": args.max_nodes,
            "beam_width": args.beam_width,
            "dps": args.dps,
            "seed": args.seed,
            "mode": args.mode,
            "const_set": args.const_set,
            "max_height": args.max_height,
            "max_radicand": args.max_radicand,
            "top_k": args.top_k,
        },
    }
    with (results_dir / "run_config.json").open("w") as fh:
        _json.dump(meta, fh, indent=2, sort_keys=True)

    console.print(
        f"[bold magenta]Run directory:[/bold magenta] {results_dir}",
    )

    all_records: list[dict] = []

    for n_val in args.n:
        target = compute_target(n_val, args.dps)
        console.print(
            f"\n[bold cyan]{'═' * 10} cos(2π/{n_val}) ≈ "
            f"{float(target):.15f} {'═' * 10}[/bold cyan]"
        )

        t0 = time.perf_counter()
        if args.mode == "beam":
            res = beam_search(
                target,
                args.max_depth,
                args.max_nodes,
                beam_width=args.beam_width,
                const_set=const_set,
                dps=args.dps,
                seed=args.seed,
                progress=args.progress,
            )
        elif args.mode == "field":
            field_max_nodes = max(args.max_nodes, 50)
            res = field_search(
                target,
                n_val,
                max_depth=args.max_depth,
                max_height=args.max_height,
                max_radicand=args.max_radicand,
                max_nodes=field_max_nodes,
                beam_width=args.beam_width,
                dps=args.dps,
                seed=args.seed,
                progress=args.progress,
            )
        else:
            res = baseline_enumerate(
                target,
                args.max_depth,
                args.max_nodes,
                const_set=const_set,
                dps=args.dps,
            )
        elapsed = time.perf_counter() - t0

        # ── display top results per depth ──
        for depth in sorted(res.keys()):
            # Show overall best at this depth level
            entries = res[depth][: args.top_k]
            if not entries:
                continue
            table = Table(
                title=f"n={n_val}  depth≤{depth}  (top {min(args.top_k, len(entries))})",
                show_lines=False,
            )
            table.add_column("#", justify="right", style="dim")
            table.add_column("Error", style="yellow")
            table.add_column("Nodes", justify="right")
            table.add_column("√-depth", justify="right")
            table.add_column("Expression")

            for rank, (err, expr) in enumerate(entries, 1):
                table.add_row(
                    str(rank),
                    f"{err:.6e}",
                    str(expr.node_count),
                    str(expr.sqrt_depth),
                    expr.to_str(),
                )
            console.print(table)

            # Show best at exactly this sqrt depth
            if depth > 0:
                exact = [
                    (e, x) for e, x in res[depth]
                    if x.sqrt_depth == depth
                ][: args.top_k]
                if exact:
                    t2 = Table(
                        title=f"  └─ best with √-depth={depth} exactly",
                        show_lines=False,
                    )
                    t2.add_column("#", justify="right", style="dim")
                    t2.add_column("Error", style="magenta")
                    t2.add_column("Nodes", justify="right")
                    t2.add_column("Expression")
                    for rank, (err, expr) in enumerate(exact, 1):
                        t2.add_row(
                            str(rank), f"{err:.6e}",
                            str(expr.node_count), expr.to_str(),
                        )
                    console.print(t2)

        # ── save JSONL ──
        jsonl_path = results_dir / f"search_n{n_val}.jsonl"
        with open(jsonl_path, "w") as fh:
            for depth, entries in sorted(res.items()):
                for rank, (err, expr) in enumerate(entries[: args.top_k], 1):
                    rec = dict(
                        n=n_val,
                        depth=depth,
                        nodes=expr.node_count,
                        sqrt_depth=expr.sqrt_depth,
                        best_error=err,
                        expression=expr.to_str(),
                        runtime=round(elapsed, 3),
                        seed=args.seed,
                        dps=args.dps,
                        rank=rank,
                    )
                    fh.write(json.dumps(rec) + "\n")
                    all_records.append(rec)

        console.print(f"[green]  → saved {jsonl_path}  ({elapsed:.1f}s)[/green]")

    # ── summary CSV (best per n × depth) ──
    csv_path = results_dir / "summary.csv"
    best: dict[tuple[int, int], dict] = {}
    for r in all_records:
        key = (r["n"], r["depth"])
        if key not in best or r["best_error"] < best[key]["best_error"]:
            best[key] = r

    fieldnames = [
        "n", "depth", "best_error", "expr", "nodes", "dps", "runtime_seconds",
    ]
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for (nv, d), r in sorted(best.items()):
            writer.writerow(
                dict(
                    n=r["n"],
                    depth=d,
                    best_error=r["best_error"],
                    expr=r["expression"],
                    nodes=r["nodes"],
                    dps=r["dps"],
                    runtime_seconds=r["runtime"],
                )
            )

    console.print(f"\n[bold green]Summary → {csv_path}[/bold green]")


if __name__ == "__main__":
    main()
