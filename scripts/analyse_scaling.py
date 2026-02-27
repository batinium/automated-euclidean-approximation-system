#!/usr/bin/env python
"""Analyse height and depth scaling from multi-run results.

Reads results/multi_run_summary.csv (produced by plot_results.py --multi-run-grid)
and individual run summaries to produce:

1. Log-log plot of best_error vs max_height per (n, depth) with fitted slopes.
2. Depth scaling plot of best_error vs depth at fixed height.
3. Paper-ready comparison tables printed to stdout and saved as CSV.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_root = Path(__file__).resolve().parent.parent


def _extract_height_from_run(run_dir: Path) -> int | None:
    cfg_path = run_dir / "run_config.json"
    if not cfg_path.exists():
        return None
    try:
        with cfg_path.open() as fh:
            cfg = json.load(fh)
        return cfg.get("args", {}).get("max_height")
    except Exception:
        return None


def _extract_max_depth_from_run(run_dir: Path) -> int | None:
    cfg_path = run_dir / "run_config.json"
    if not cfg_path.exists():
        return None
    try:
        with cfg_path.open() as fh:
            cfg = json.load(fh)
        return cfg.get("args", {}).get("max_depth")
    except Exception:
        return None


def _load_height_scaling_data(results_root: Path) -> pd.DataFrame:
    """Load best errors from height scaling runs."""
    rows = []
    for run_dir in sorted(results_root.iterdir()):
        if not run_dir.is_dir():
            continue
        if not re.match(r"field_n[\d-]+_d2_h\d+", run_dir.name):
            continue
        height = _extract_height_from_run(run_dir)
        if height is None:
            continue
        summary = run_dir / "summary.csv"
        if not summary.exists():
            continue
        df = pd.read_csv(summary)
        for _, row in df.iterrows():
            rows.append({
                "n": int(row["n"]),
                "depth": int(row["depth"]),
                "max_height": height,
                "best_error": float(row["best_error"]),
                "expression": row.get("expr", ""),
            })
    return pd.DataFrame(rows)


def _load_depth_scaling_data(results_root: Path) -> pd.DataFrame:
    """Load best errors from depth scaling runs (h=32 only)."""
    rows = []
    for run_dir in sorted(results_root.iterdir()):
        if not run_dir.is_dir():
            continue
        if not run_dir.name.startswith("field_n7-11-13_d"):
            continue
        if "h32" not in run_dir.name:
            continue
        max_depth = _extract_max_depth_from_run(run_dir)
        if max_depth is None:
            continue
        summary = run_dir / "summary.csv"
        if not summary.exists():
            continue
        df = pd.read_csv(summary)
        for _, row in df.iterrows():
            rows.append({
                "n": int(row["n"]),
                "max_depth": max_depth,
                "depth": int(row["depth"]),
                "best_error": float(row["best_error"]),
                "expression": row.get("expr", ""),
            })
    return pd.DataFrame(rows)


def _load_multi_run_summary(results_root: Path) -> pd.DataFrame:
    """Load multi-run summary produced by plot_results.py --multi-run-grid."""
    csv_path = results_root / "multi_run_summary.csv"
    if not csv_path.exists():
        return pd.DataFrame()
    return pd.read_csv(csv_path)


def plot_height_scaling(df: pd.DataFrame, out_dir: Path) -> None:
    """Log-log plot of best_error vs max_height, one subplot per (n, depth)."""
    if df.empty:
        print("No height scaling data to plot.")
        return

    ns = sorted(df["n"].unique())
    depths = sorted(df["depth"].unique())
    # Only plot depths where error actually varies with height
    depths = [d for d in depths if d > 0]

    ncols = len(ns)
    nrows = len(depths)
    if ncols == 0 or nrows == 0:
        return

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows), squeeze=False)

    for ri, d in enumerate(depths):
        for ci, n in enumerate(ns):
            ax = axes[ri][ci]
            sub = df[(df["n"] == n) & (df["depth"] == d)].sort_values("max_height")
            if sub.empty:
                ax.set_visible(False)
                continue

            h = sub["max_height"].values
            e = sub["best_error"].values

            ax.loglog(h, e, "o-", lw=2, ms=6, color=f"C{ci}")

            # Fit slope in log-log space
            if len(h) >= 2:
                log_h = np.log10(h.astype(float))
                log_e = np.log10(e)
                coeffs = np.polyfit(log_h, log_e, 1)
                slope = coeffs[0]
                fit_e = 10 ** np.polyval(coeffs, log_h)
                ax.loglog(h, fit_e, "--", color="gray", alpha=0.7)
                ax.text(
                    0.05, 0.05,
                    f"slope = {slope:.2f}",
                    transform=ax.transAxes,
                    fontsize=10,
                    verticalalignment="bottom",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.5),
                )

            ax.set_xlabel("max_height")
            ax.set_ylabel("best |error|")
            ax.set_title(f"n={n}, depth {d}")
            ax.grid(True, alpha=0.3, which="both")

    fig.suptitle("Height Scaling: best error vs max_height (log-log)", fontsize=14, y=1.02)
    fig.tight_layout()
    out_path = out_dir / "height_scaling_loglog.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")


def plot_depth_scaling(df: pd.DataFrame, out_dir: Path) -> None:
    """Semilogy plot of best_error vs depth for each n at max_depth=max(depth)."""
    if df.empty:
        print("No depth scaling data to plot.")
        return

    # For each n, take the best error at each actual depth across all max_depth runs
    best = df.groupby(["n", "depth"])["best_error"].min().reset_index()
    ns = sorted(best["n"].unique())

    fig, ax = plt.subplots(figsize=(7, 5))
    for n in ns:
        sub = best[best["n"] == n].sort_values("depth")
        ax.semilogy(sub["depth"], sub["best_error"], "o-", lw=2, ms=7, label=f"n={n}")

    ax.set_xlabel("sqrt depth")
    ax.set_ylabel("best |error|")
    ax.set_title("Depth Scaling at height=32 (field search)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path = out_dir / "depth_scaling_h32.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")


def _field_vs_beam_pivot(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.pivot_table(
        index=["n", "depth"],
        columns="run_mode",
        values="best_error",
        aggfunc="min",
    )
    if "field" in pivot.columns and "beam" in pivot.columns:
        pivot["field_wins"] = pivot["field"] < pivot["beam"]
        pivot["ratio"] = pivot["beam"] / pivot["field"]
    return pivot


def _pick_baseline_runs(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """Pick canonical baseline run names from multi-run summary.

    Preference order:
    1) Exact canonical names.
    2) Non-justif runs matching canonical labels.
    """
    if df.empty:
        return None, None

    runs = set(df["run"].unique())
    beam_exact = "beam_n7-11-13_d3_nodes15_bw2000"
    field_exact = "field_n7-11-13_d3_h20_r30_bw2000"
    beam_run = beam_exact if beam_exact in runs else None
    field_run = field_exact if field_exact in runs else None

    if beam_run is None:
        cand = sorted(
            r for r in runs
            if r.startswith("beam_") and not r.startswith("justif_")
        )
        beam_run = cand[0] if cand else None
    if field_run is None:
        cand = sorted(
            r for r in runs
            if r.startswith("field_") and not r.startswith("justif_")
            and "_h20_" in r and "_d3_" in r
        )
        field_run = cand[0] if cand else None

    return beam_run, field_run


def print_field_vs_beam_tables(df: pd.DataFrame, out_dir: Path) -> None:
    """Print and save both baseline and best-of field-vs-beam tables."""
    if df.empty:
        print("No field vs beam data available.")
        return

    # Best-of comparison across all runs in each mode
    bestof_df = df[df["run_mode"].isin(["beam", "field"])].copy()
    bestof_pivot = _field_vs_beam_pivot(bestof_df)
    print("\n=== Field vs Beam Comparison (Best-Of By Mode) ===\n")
    print(bestof_pivot.to_string(float_format=lambda x: f"{x:.3e}" if isinstance(x, float) else str(x)))
    bestof_csv = out_dir / "field_vs_beam_bestof_table.csv"
    bestof_pivot.to_csv(bestof_csv)
    print(f"\nSaved {bestof_csv}")

    # Baseline-only comparison (canonical pair)
    beam_run, field_run = _pick_baseline_runs(df)
    if beam_run is None or field_run is None:
        print("\nCould not identify canonical baseline runs; skipping baseline-only table.")
        return
    baseline_df = df[df["run"].isin([beam_run, field_run])].copy()
    baseline_pivot = _field_vs_beam_pivot(baseline_df)
    print("\n=== Field vs Beam Comparison (Baseline Runs Only) ===\n")
    print(f"Using beam run:  {beam_run}")
    print(f"Using field run: {field_run}\n")
    print(baseline_pivot.to_string(float_format=lambda x: f"{x:.3e}" if isinstance(x, float) else str(x)))

    baseline_csv = out_dir / "field_vs_beam_baseline_table.csv"
    baseline_pivot.to_csv(baseline_csv)
    print(f"\nSaved {baseline_csv}")

    # Backward-compatible filename now points to baseline-only table
    compat_csv = out_dir / "field_vs_beam_table.csv"
    baseline_pivot.to_csv(compat_csv)
    print(f"Saved {compat_csv} (baseline-only, backward-compatible name)")


def print_height_scaling_table(df: pd.DataFrame, out_dir: Path) -> None:
    """Print and save height scaling table."""
    if df.empty:
        print("No height scaling data available.")
        return

    print("\n=== Height Scaling Summary (RQ1) ===\n")
    depths = sorted(df["depth"].unique())
    for d in depths:
        if d == 0:
            continue
        sub = df[df["depth"] == d]
        pivot = sub.pivot_table(
            index="max_height",
            columns="n",
            values="best_error",
            aggfunc="min",
        )
        print(f"--- Depth {d} ---")
        print(pivot.to_string(float_format=lambda x: f"{x:.3e}"))
        print()

    csv_path = out_dir / "height_scaling_table.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")


def print_depth_scaling_table(df: pd.DataFrame, out_dir: Path) -> None:
    """Print depth scaling table with improvement ratios."""
    if df.empty:
        print("No depth scaling data available.")
        return

    best = df.groupby(["n", "depth"])["best_error"].min().reset_index()

    print("\n=== Depth Scaling Summary (RQ1/RQ2) at height=32 ===\n")
    ns = sorted(best["n"].unique())
    for n in ns:
        sub = best[best["n"] == n].sort_values("depth")
        print(f"n={n}:")
        prev_err = None
        for _, row in sub.iterrows():
            d = int(row["depth"])
            err = row["best_error"]
            ratio_str = ""
            if prev_err is not None and err > 0:
                ratio = prev_err / err
                ratio_str = f"  ({ratio:.1f}x improvement)"
            print(f"  depth {d}: {err:.3e}{ratio_str}")
            prev_err = err
        print()

    csv_path = out_dir / "depth_scaling_table.csv"
    best.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")


def _load_saturation_data(
    results_root: Path, target_ns: list[int] = (7, 11, 13),
) -> dict[int, dict[int, dict[int, float]]]:
    """Load best errors for each n at different heights and depths.

    Returns {n: {height: {depth: best_error}}}.
    """
    data: dict[int, dict[int, dict[int, float]]] = {n: {} for n in target_ns}

    for run_dir in sorted(results_root.iterdir()):
        if not run_dir.is_dir():
            continue
        cfg_path = run_dir / "run_config.json"
        if not cfg_path.exists():
            continue
        try:
            with cfg_path.open() as fh:
                cfg = json.load(fh)
            args = cfg.get("args", {})
            if args.get("mode") != "field":
                continue
            height = args.get("max_height")
            if height is None:
                continue
        except Exception:
            continue

        for n in target_ns:
            for p in run_dir.glob(f"search_n{n}.jsonl"):
                with open(p) as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        rec = json.loads(line)
                        dep = rec["depth"]
                        err = rec["best_error"]
                        data[n].setdefault(height, {})
                        if dep not in data[n][height] or err < data[n][height][dep]:
                            data[n][height][dep] = err

    return data


def plot_saturation(results_root: Path, out_dir: Path) -> None:
    """Plot best_error vs depth for n=7,11,13 at h=32 vs h=64, showing saturation."""
    all_data = _load_saturation_data(results_root)
    highlight_heights = [32, 64]
    target_ns = [n for n in [7, 11, 13] if all_data.get(n)]

    any_plotted = False
    fig, axes = plt.subplots(1, len(target_ns), figsize=(5 * len(target_ns), 5),
                             squeeze=False)

    for col, n in enumerate(target_ns):
        ax = axes[0, col]
        ndata = all_data[n]
        available = [h for h in highlight_heights if h in ndata]
        if len(available) < 2:
            ax.set_title(f"n={n} (insufficient data)")
            continue
        any_plotted = True
        markers = ["o", "s", "D", "^", "v"]
        for i, h in enumerate(sorted(available)):
            depths = sorted(ndata[h].keys())
            errors = [ndata[h][d] for d in depths]
            ax.semilogy(
                depths, errors, f"{markers[i % len(markers)]}-",
                lw=2, ms=7, label=f"height = {h}",
            )
            sat_depth = None
            for j in range(1, len(depths)):
                if errors[j] >= errors[j - 1] * 0.99:
                    sat_depth = depths[j]
                    break
            if sat_depth is not None:
                ax.axvline(sat_depth - 0.05 + i * 0.1, color=f"C{i}",
                           ls=":", alpha=0.5, lw=1.5)

        ax.set_xlabel("sqrt depth")
        ax.set_ylabel("best |error|")
        ax.set_title(f"n={n}")
        ax.set_xticks(range(5))
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    if not any_plotted:
        print("Need h=32 and h=64 runs for at least one n to produce saturation figure.")
        plt.close(fig)
        return

    fig.suptitle("Depth Saturation: coefficient resolution floor (h=32 vs h=64)",
                 fontsize=13, y=1.02)
    fig.tight_layout()
    out_path = out_dir / "saturation_h32_vs_h64.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")

    print("\n=== Saturation Analysis (h=32 vs h=64) ===\n")
    rows = []
    for n in target_ns:
        ndata = all_data[n]
        available = sorted(h for h in highlight_heights if h in ndata)
        if not available:
            continue
        print(f"  n={n}")
        print(f"  {'depth':<8}", end="")
        for h in available:
            print(f"{'h=' + str(h):<14}", end="")
        print(f"{'ratio (32/64)':<14}")
        print(f"  " + "-" * (8 + 14 * len(available) + 14))
        all_depths = sorted(set().union(*(ndata[h].keys() for h in available)))
        for d in all_depths:
            print(f"  {d:<8}", end="")
            vals = {}
            for h in available:
                v = ndata[h].get(d)
                vals[h] = v
                print(f"{v:.3e}       " if v is not None else "n/a           ", end="")
            if vals.get(32) and vals.get(64) and vals[64] > 0:
                print(f"{vals[32] / vals[64]:.1f}x", end="")
            print()
            for h in available:
                if vals[h] is not None:
                    rows.append({"n": n, "height": h, "depth": d, "best_error": vals[h]})
        print()

    csv_path = out_dir / "saturation_table.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Analyse scaling from AEAS experiment results.")
    ap.add_argument("--root", type=str, default="results", help="Results root directory.")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"No such directory: {root}")
        return

    out_dir = root / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Height scaling
    height_df = _load_height_scaling_data(root)
    plot_height_scaling(height_df, out_dir)
    print_height_scaling_table(height_df, out_dir)

    # Depth scaling
    depth_df = _load_depth_scaling_data(root)
    plot_depth_scaling(depth_df, out_dir)
    print_depth_scaling_table(depth_df, out_dir)

    # Field vs beam (best-of + baseline-only)
    fvb_df = _load_multi_run_summary(root)
    print_field_vs_beam_tables(fvb_df, out_dir)

    # Saturation analysis
    plot_saturation(root, out_dir)


if __name__ == "__main__":
    main()
