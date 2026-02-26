#!/usr/bin/env python
"""Visualise AEAS search results saved by run_search.py."""

from __future__ import annotations

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


def main() -> None:
    results_dir = Path("results")
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
        print("No results found in results/. Run run_search.py first.")
        return

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
        ax.semilogy(sub["nodes"], sub["best_error"], "o", alpha=0.45, ms=3.5, color="C1")
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
