#!/usr/bin/env python
"""Visualise AEAS search results saved by run_search.py."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

_root = Path(__file__).resolve().parent.parent
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))


def _pick_results_dir(root: Path, run: str | None) -> Path:
    """Choose which results directory to visualise.

    - If *run* is provided → root / run.
    - Else, if any subdirectories under *root* contain search_n*.jsonl,
      pick the most recently modified such directory.
    - Else, fall back to *root* itself.
    """
    if run:
        return root / run

    root = root.resolve()
    candidates: list[tuple[float, Path]] = []

    for sub in root.iterdir():
        if not sub.is_dir():
            continue
        if any(sub.glob("search_n*.jsonl")):
            candidates.append((sub.stat().st_mtime, sub))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    return root


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Plot AEAS search results saved by run_search.py.",
    )
    ap.add_argument(
        "--root",
        type=str,
        default="results",
        help="Root directory containing run subdirectories.",
    )
    ap.add_argument(
        "--run",
        type=str,
        default=None,
        help="Specific run subdirectory under --root to plot. "
        "If omitted, the most recent run is used.",
    )
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"No such results root: {root}")
        return

    results_dir = _pick_results_dir(root, args.run)
    figures_dir = results_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    for p in sorted(results_dir.glob("search_n*.jsonl")):
        with open(p) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    if not records:
        print(
            f"No results found in {results_dir}. "
            "Run scripts/run_search.py first.",
        )
        return

    print(f"Using results from: {results_dir}")

    df = pd.DataFrame(records)
    ns = sorted(df["n"].unique())

    # ── Plot 1: best error vs sqrt depth per n ──
    ncols = max(len(ns), 1)
    fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 4.5), squeeze=False)
    for i, n in enumerate(ns):
        ax = axes[0][i]
        sub = df[df["n"] == n]
        best = sub.groupby("depth")["best_error"].min()
        ax.semilogy(best.index, best.values, "o-", lw=2, ms=7, color="C0")
        ax.set_xlabel("sqrt depth")
        ax.set_ylabel("best |error|")
        ax.set_title(f"cos(2π/{n})")
        ax.grid(True, alpha=0.3)
    fig.suptitle("Approximation Error vs sqrt Depth", fontsize=13, y=1.02)
    fig.tight_layout()
    path1 = figures_dir / "error_vs_depth.png"
    fig.savefig(path1, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path1}")

    # ── Plot 2: error vs node count per n ──
    fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 4.5), squeeze=False)
    for i, n in enumerate(ns):
        ax = axes[0][i]
        sub = df[df["n"] == n]
        ax.semilogy(
            sub["nodes"],
            sub["best_error"],
            "o",
            alpha=0.45,
            ms=3.5,
            color="C1",
        )
        ax.set_xlabel("node count")
        ax.set_ylabel("|error|")
        ax.set_title(f"cos(2π/{n})")
        ax.grid(True, alpha=0.3)
    fig.suptitle("Approximation Error vs Node Count", fontsize=13, y=1.02)
    fig.tight_layout()
    path2 = figures_dir / "error_vs_nodes.png"
    fig.savefig(path2, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path2}")

    # ── Plot 3: combined best errors (all n on one axes) ──
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for n in ns:
        sub = df[df["n"] == n]
        best = sub.groupby("depth")["best_error"].min()
        ax.semilogy(best.index, best.values, "o-", lw=2, ms=7, label=f"n={n}")
    ax.set_xlabel("sqrt depth")
    ax.set_ylabel("best |error|")
    ax.set_title("Best Constructible Approximation Error")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path3 = figures_dir / "combined_errors.png"
    fig.savefig(path3, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path3}")


if __name__ == "__main__":
    main()
