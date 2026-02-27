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
import math

_root = Path(__file__).resolve().parent.parent
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from aeas.evaluate import compute_target  # noqa: E402


def _load_run_config(run_dir: Path) -> dict | None:
    p = run_dir / "run_config.json"
    if not p.exists():
        return None
    try:
        with p.open() as fh:
            return json.load(fh)
    except Exception:
        return None


def _format_run_label(run_dir: Path) -> str:
    cfg = _load_run_config(run_dir)
    if not cfg or "args" not in cfg:
        return run_dir.name
    a = cfg["args"]
    mode = a.get("mode", "?")
    bw = a.get("beam_width", "?")
    md = a.get("max_depth", "?")

    if mode == "field":
        mh = a.get("max_height", "?")
        mr = a.get("max_radicand", "?")
        return f"field d{md} bw{bw} h{mh} r{mr}"
    if mode == "beam":
        mn = a.get("max_nodes", "?")
        return f"beam d{md} bw{bw} nodes{mn}"
    if mode == "baseline":
        mn = a.get("max_nodes", "?")
        return f"baseline d{md} nodes{mn}"
    return f"{mode} d{md} bw{bw}"


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


def _iter_run_dirs(root: Path) -> list[Path]:
    """Return all run directories under *root* that contain search_n*.jsonl."""
    root = root.resolve()
    runs: list[Path] = []
    for sub in sorted(root.iterdir()):
        if not sub.is_dir():
            continue
        if any(sub.glob("search_n*.jsonl")):
            runs.append(sub)
    return runs


def _plot_multi_run_grid(root: Path, run_dirs: list[Path]) -> None:
    """Plot a cross-run grid of best errors vs sqrt depth.

    Each subplot corresponds to a target n, and within each subplot we show
    the best error curve for every run directory under *root*.  This is
    useful for comparing different algorithms / parameter sweeps (e.g.
    beam vs field, different beam_width / max_height values) at a glance.
    """
    records: list[dict] = []
    run_meta: dict[str, dict] = {}
    for rd in run_dirs:
        run_name = rd.name
        run_meta[run_name] = {
            "label": _format_run_label(rd),
            "config": _load_run_config(rd),
        }
        for p in sorted(rd.glob("search_n*.jsonl")):
            with open(p) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        rec = json.loads(line)
                        rec["run"] = run_name
                        rec["run_label"] = run_meta[run_name]["label"]
                        cfg = run_meta[run_name]["config"]
                        if cfg and "args" in cfg:
                            rec["run_mode"] = cfg["args"].get("mode")
                        records.append(rec)

    if not records:
        print(
            f"No aggregated records found under {root} "
            "(no search_n*.jsonl files).",
        )
        return

    df = pd.DataFrame(records)
    ns = sorted(df["n"].unique())
    run_labels = (
        df[["run", "run_label"]]
        .drop_duplicates()
        .sort_values(["run_label", "run"])
        .to_dict("records")
    )

    ncols = max(len(ns), 1)
    fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 4.5), squeeze=False)

    for i, n in enumerate(ns):
        ax = axes[0][i]
        sub = df[df["n"] == n]
        for rl in run_labels:
            run_name = rl["run"]
            label = rl["run_label"]
            rsub = sub[sub["run"] == run_name]
            if rsub.empty:
                continue
            best = rsub.groupby("depth")["best_error"].min()
            ax.semilogy(
                best.index,
                best.values,
                "o-",
                lw=2,
                ms=5,
                label=label,
            )
        ax.set_xlabel("sqrt depth")
        ax.set_ylabel("best |error|")
        ax.set_title(f"cos(2π/{n})")
        ax.grid(True, alpha=0.3)
        if i == len(ns) - 1:
            # Place legend once, on the last subplot to avoid clutter.
            ax.legend(fontsize=7, loc="upper right")

    fig.suptitle(
        "Best Constructible Approximation Error — multi-run grid",
        fontsize=13,
        y=1.02,
    )
    fig.tight_layout()
    out_path = root / "multi_run_error_vs_depth.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")

    # Also emit an aggregated CSV for programmatic comparison.
    # One row per (run, n, depth) with the best error and the expression that achieved it.
    cols = ["run", "run_label", "run_mode", "n", "depth", "best_error", "expression", "nodes", "sqrt_depth", "dps", "runtime"]
    # For each (run,n,depth), pick the row with minimal best_error (rank may not be 1 if input contains mixed records).
    gb = df.sort_values("best_error").groupby(["run", "n", "depth"], as_index=False).first()
    for c in cols:
        if c not in gb.columns:
            gb[c] = None
    gb = gb[cols].sort_values(["n", "depth", "best_error", "run_label"])
    csv_path = root / "multi_run_summary.csv"
    gb.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")


def _plot_one_dir(results_dir: Path) -> None:
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

    # ── Plot 4: n-gon closure drift from cos(2π/n) approximations ──
    #
    # For each n, we compare the exact regular n-gon (using the true
    # angle 2π/n) with polygons built from an approximate angle inferred
    # from the best available cos(2π/n) at several depths. We do not
    # reconstruct the exact expression value; instead we perturb the
    # true cos by the recorded best_error, which is more than enough to
    # visualise how angle errors would accumulate around the circle.
    fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 5), squeeze=False)
    for i, n in enumerate(ns):
        ax = axes[0][i]
        sub = df[df["n"] == n]
        depths = sorted(sub["depth"].unique())
        if not depths:
            continue

        # Choose a small representative set of depths: min / mid / max.
        rep_depths = sorted(
            set(
                [
                    depths[0],
                    depths[len(depths) // 2],
                    depths[-1],
                ]
            )
        )

        # Exact reference polygon on the unit circle.
        c_true = float(compute_target(int(n), 80))
        theta_true = 2.0 * math.pi / int(n)
        xs_true = [math.cos(k * theta_true) for k in range(int(n) + 1)]
        ys_true = [math.sin(k * theta_true) for k in range(int(n) + 1)]
        ax.plot(xs_true, ys_true, "-k", lw=2, label="exact")

        colors = ["C1", "C2", "C3", "C4", "C5"]
        for j, d in enumerate(rep_depths):
            dsub = sub[sub["depth"] == d]
            if dsub.empty:
                continue
            best_err = float(dsub["best_error"].min())
            # Approximate cos value as true ± error. We do not know the
            # original sign, but for small errors the magnitude dominates
            # the geometric effect; take a consistent convention.
            c_approx = c_true + best_err
            c_approx = max(min(c_approx, 1.0), -1.0)
            theta_approx = math.acos(c_approx)

            xs = [math.cos(k * theta_approx) for k in range(int(n) + 1)]
            ys = [math.sin(k * theta_approx) for k in range(int(n) + 1)]
            ax.plot(
                xs,
                ys,
                "-",
                lw=1.4,
                color=colors[j % len(colors)],
                label=f"depth={d}",
            )

        ax.set_aspect("equal", "box")
        ax.set_title(f"n={n} polygon drift")
        ax.axis("off")
        ax.legend(fontsize=8, loc="upper right")

    fig.suptitle(
        "Regular n-gon closure drift from cos(2π/n) approximations",
        fontsize=13,
        y=1.02,
    )
    fig.tight_layout()
    path4 = figures_dir / "ngon_drift.png"
    fig.savefig(path4, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path4}")


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
        "If omitted (and --all-runs is not given), the most recent run is used.",
    )
    ap.add_argument(
        "--all-runs",
        action="store_true",
        help="Generate figures for every run directory under --root that "
        "contains search_n*.jsonl.",
    )
    ap.add_argument(
        "--multi-run-grid",
        action="store_true",
        help=(
            "Generate a single cross-run grid figure (best error vs sqrt depth) "
            "using all run subdirectories under --root."
        ),
    )
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"No such results root: {root}")
        return

    # Optional aggregated multi-run grid (across all run directories).
    if args.multi_run_grid:
        run_dirs = _iter_run_dirs(root)
        if not run_dirs:
            print(f"No run directories with search_n*.jsonl under {root}")
        else:
            _plot_multi_run_grid(root, run_dirs)

    if args.all_runs:
        run_dirs = _iter_run_dirs(root)
        if not run_dirs:
            print(f"No run directories with search_n*.jsonl under {root}")
            return
        for rd in run_dirs:
            _plot_one_dir(rd)
    else:
        results_dir = _pick_results_dir(root, args.run)
        _plot_one_dir(results_dir)


if __name__ == "__main__":
    main()
