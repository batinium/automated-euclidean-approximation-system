#!/usr/bin/env python
"""
Additional visualisations for the AEAS paper.

This script focuses on *algorithm* visualisations rather than just result
curves.  It can generate:

1. A high-level architecture diagram of the field-first search pipeline.
2. Expression-tree diagrams for specific best candidates from a run.
3. A depth‑1 search heatmap for A + B·√m, showing the guided coefficient search.
4. A simple “tower layers” overview based on the depth-scaling table.

All figures are emitted as PNGs suitable for inclusion in the paper.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

import mpmath

import sys

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from aeas.evaluate import compute_target


# ── 1. Architecture diagram ──────────────────────────────────────────────────


def _draw_box(
    ax: plt.Axes,
    center: Tuple[float, float],
    width: float,
    height: float,
    text: str,
    fontsize: int = 10,
    facecolor: str = "#f0f0ff",
) -> None:
    cx, cy = center
    x = cx - width / 2
    y = cy - height / 2
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.2",
        linewidth=1.0,
        edgecolor="#303050",
        facecolor=facecolor,
    )
    ax.add_patch(box)
    ax.text(
        cx,
        cy,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
    )


def _draw_arrow(
    ax: plt.Axes,
    xy_from: Tuple[float, float],
    xy_to: Tuple[float, float],
    text: Optional[str] = None,
    fontsize: int = 9,
) -> None:
    arrow = FancyArrowPatch(
        xy_from,
        xy_to,
        arrowstyle="->",
        mutation_scale=10,
        linewidth=1.0,
        color="#303050",
    )
    ax.add_patch(arrow)
    if text:
        mx = (xy_from[0] + xy_to[0]) / 2
        my = (xy_from[1] + xy_to[1]) / 2
        ax.text(mx, my, text, fontsize=fontsize, ha="center", va="center")


def plot_architecture(out_path: Path) -> None:
    """High-level field-first search architecture diagram."""
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")

    # Row 1: target + depth-0 rationals
    _draw_box(ax, (1.5, 4.5), 2.0, 0.9, "Target\ncos(2π/n)", facecolor="#fff5e6")
    _draw_box(
        ax,
        (5.5, 4.5),
        3.0,
        0.9,
        "Depth 0:\nRationals A (height ≤ H)",
    )

    # Row 2: depth-1 guided search
    _draw_box(
        ax,
        (9.5, 4.5),
        3.2,
        0.9,
        "Depth 1:\nA + B·√m, squarefree m ≤ M\nguided coefficient search",
    )

    # Row 3: float pre-filter
    _draw_box(
        ax,
        (3.0, 2.5),
        4.0,
        0.9,
        "Float pre-filter over millions of\n(A, B, m) / (P, Q, inner) tuples",
        facecolor="#e6f7ff",
    )

    # Row 4: tree materialisation + pruning
    _draw_box(
        ax,
        (9.5, 2.5),
        3.6,
        0.9,
        "Tree materialisation + mpmath\n+ diversity-preserving pruning",
        facecolor="#e6ffe6",
    )

    # Row 5: deeper tower levels
    _draw_box(
        ax,
        (6.5, 0.8),
        5.0,
        1.1,
        "Depth ≥2 towers:\nP + Q·√(inner depth d−1),\nbiquadratic corrections C·√n",
    )

    # Arrows
    _draw_arrow(ax, (2.5, 4.5), (3.5, 4.5), None)
    _draw_arrow(ax, (7.0, 4.5), (8.2, 4.5), None)
    _draw_arrow(ax, (9.5, 3.9), (9.5, 3.1), "best float\ncandidates")
    _draw_arrow(ax, (3.0, 3.9), (3.0, 3.1), "target\nprojection")
    _draw_arrow(ax, (5.0, 3.9), (3.8, 3.1), None)
    _draw_arrow(ax, (9.5, 1.9), (7.2, 1.4), "survivors\nper depth")
    _draw_arrow(ax, (5.8, 1.4), (9.0, 1.9), "inner values\nfor next depth")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


# ── 2. Expression-tree diagram ───────────────────────────────────────────────


@dataclass
class _ParsedNode:
    label: str
    children: List["_ParsedNode"]


def _parse_expr_string(s: str) -> _ParsedNode:
    """Parse the ExprNode.to_str() representation into a simple tree.

    Grammar covered:
    - integers, e.g. 3 or -5
    - fractions: (p/q)
    - binary ops: (left + right), (left - right), (left * right), (left / right)
    - unary sqrt: sqrt(inner)
    """

    s = s.strip()

    # sqrt(inner)
    if s.startswith("sqrt(") and s.endswith(")"):
        inner = s[len("sqrt(") : -1]
        return _ParsedNode("√", [_parse_expr_string(inner)])

    # Remove outer parens if present
    if s.startswith("(") and s.endswith(")"):
        inner = s[1:-1]
        # Fractions have no spaces inside "(p/q)"
        if " " not in inner:
            return _ParsedNode(inner, [])

        # Otherwise we have a binary op of the form "left <op> right"
        # with spaces around the operator, fully parenthesised.
        depth = 0
        for i in range(len(inner)):
            ch = inner[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif depth == 0 and i + 2 < len(inner):
                token = inner[i : i + 3]
                if token in (" + ", " - ", " * ", " / "):
                    left = inner[:i]
                    op = token.strip()
                    right = inner[i + 3 :]
                    return _ParsedNode(
                        op,
                        [
                            _parse_expr_string(left),
                            _parse_expr_string(right),
                        ],
                    )

    # Fallback: treat as atomic label
    return _ParsedNode(s, [])


def _layout_tree(
    node: _ParsedNode, depth: int = 0, x_offset: float = 0.0
) -> Tuple[List[Tuple[_ParsedNode, float, int]], float]:
    """Assign x positions by recursive in-order layout.

    Returns (placements, next_x_offset).
    """
    if not node.children:
        return ([(node, x_offset, depth)], x_offset + 1.0)

    placements: List[Tuple[_ParsedNode, float, int]] = []
    child_xs: List[float] = []
    x = x_offset
    for ch in node.children:
        ch_places, x = _layout_tree(ch, depth + 1, x)
        placements.extend(ch_places)
        # average x of this child subtree
        xs = [px for (_, px, _) in ch_places]
        child_xs.append(sum(xs) / len(xs))

    cx = sum(child_xs) / len(child_xs)
    placements.append((node, cx, depth))
    return placements, x


def plot_expression_tree(
    run_dir: Path,
    n: int,
    depth_level: int,
    rank: int,
    out_path: Path,
) -> None:
    """Plot the expression tree for a specific candidate from a run."""
    search_path = run_dir / f"search_n{n}.jsonl"
    if not search_path.exists():
        raise FileNotFoundError(search_path)

    expr_str: Optional[str] = None
    with search_path.open() as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("depth") == depth_level and rec.get("rank") == rank:
                expr_str = rec.get("expression")
                break
    if not expr_str:
        raise RuntimeError(
            f"No expression found for n={n}, depth={depth_level}, rank={rank}"
        )

    root = _parse_expr_string(expr_str)
    placements, _ = _layout_tree(root)

    xs = [x for (_, x, _) in placements]
    ys = [d for (_, _, d) in placements]
    max_depth = max(ys) if ys else 0

    fig, ax = plt.subplots(figsize=(6, 3 + 0.7 * max_depth))
    ax.axis("off")

    # draw edges
    pos = {id(node): (x, -d) for (node, x, d) in placements}
    for node, x, d in placements:
        for child in node.children:
            cx, cy = pos[id(child)]
            ax.plot([x, cx], [-d, cy], color="#999999", linewidth=1.0)

    # draw nodes
    for node, x, d in placements:
        y = -d
        # circle
        ax.scatter([x], [y], s=80, color="#ffffff", edgecolor="#333333", zorder=3)
        # label slightly below the circle to improve readability
        ax.text(
            x,
            y - 0.22,
            node.label,
            fontsize=8,
            ha="center",
            va="top",
            zorder=4,
        )

    ax.set_title(f"Expression tree for n={n}, depth={depth_level}, rank={rank}")
    ax.set_ylim(-max_depth - 1, 1)
    ax.set_xlim(min(xs) - 1, max(xs) + 1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


# ── 3. Depth‑1 guided search heatmap ────────────────────────────────────────


def plot_depth1_heatmap(
    n: int,
    m: int,
    max_height: int,
    out_path: Path,
    lo: float = -2.5,
    hi: float = 2.5,
) -> None:
    """Visualise the A + B·√m depth‑1 search as a heatmap over (A, B).

    We restrict A and B to reduced rationals p/q with denominator ≤ max_height
    and value in [lo, hi].  For each (A, B) we compute |A + B·√m − cos(2π/n)|.
    """
    with mpmath.workdps(80):
        target = float(compute_target(n, dps=80))
        s = float(mpmath.sqrt(m))

    # Build discrete grids of rational A, B (values, not distinct fractions).
    vals = set()
    for q in range(1, max_height + 1):
        p_lo = int(np.ceil(lo * q))
        p_hi = int(np.floor(hi * q))
        for p in range(p_lo, p_hi + 1):
            vals.add(p / q)
    grid_vals = sorted(vals)

    A = np.array(grid_vals)
    B = np.array(grid_vals)
    AA, BB = np.meshgrid(A, B, indexing="xy")
    X = AA + BB * s
    err = np.abs(X - target)

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(
        np.log10(err + 1e-16),
        origin="lower",
        extent=[A[0], A[-1], B[0], B[-1]],
        aspect="auto",
        cmap="viridis_r",
    )
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("log10 |A + B·√m − cos(2π/n)|")

    ax.set_xlabel("A (rational)")
    ax.set_ylabel("B (rational coefficient of √m)")
    ax.set_title(f"Depth‑1 search landscape for n={n}, m={m}, height ≤ {max_height}")
    ax.grid(False)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


# ── 4. Tower “layers” overview based on depth-scaling table ─────────────────


def plot_tower_layers(
    depth_scaling_csv: Path,
    n: int,
    out_path: Path,
) -> None:
    """Simple layered diagram summarising best error vs depth for a single n."""
    import pandas as pd

    df = pd.read_csv(depth_scaling_csv)
    df_n = df[df["n"] == n].sort_values("depth")
    if df_n.empty:
        raise RuntimeError(f"No rows for n={n} in {depth_scaling_csv}")

    depths = df_n["depth"].values
    errs = df_n["best_error"].values
    log_errs = -np.log10(errs)
    max_x = float(np.max(log_errs))

    fig, ax = plt.subplots(figsize=(5, 3 + 0.5 * len(depths)))
    y = np.arange(len(depths))[::-1]  # depth 0 at top

    ax.hlines(y, 0, log_errs, color="#4c72b0", linewidth=3)
    ax.scatter(log_errs, y, color="#4c72b0", zorder=3)

    for yi, d, e, xe in zip(y, depths, errs, log_errs):
        ax.text(
            xe + 0.2,
            yi,
            f"depth {d}: error {e:.1e}",
            va="center",
            ha="left",
            fontsize=9,
        )

    ax.set_yticks([])
    ax.set_xlabel("−log10(error)")
    ax.set_title(f"Best error per sqrt‑depth for n={n}")
    ax.set_xlim(0, max_x * 1.4)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


# ── CLI entry point ─────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Visualise AEAS search algorithm and representative expressions.",
    )
    ap.add_argument(
        "--root",
        type=str,
        default="results",
        help="Results root directory (default: results).",
    )
    ap.add_argument(
        "--mode",
        type=str,
        default="all",
        choices=["all", "architecture", "expr-tree", "heatmap", "layers"],
        help="Which visualisation to generate.",
    )
    ap.add_argument("--n", type=int, default=7, help="Target n for expr/heatmap/layers.")
    ap.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Depth level for expression-tree visualisation.",
    )
    ap.add_argument(
        "--rank",
        type=int,
        default=1,
        help="Rank within the depth for expression-tree visualisation.",
    )
    ap.add_argument(
        "--m",
        type=int,
        default=2,
        help="Radicand m for A + B·√m heatmap (depth‑1 illustration).",
    )
    ap.add_argument(
        "--max-height",
        type=int,
        default=32,
        help="Max coefficient height for the depth‑1 heatmap.",
    )
    args = ap.parse_args()

    root = Path(args.root)
    out_dir = root / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode in ("all", "architecture"):
        plot_architecture(out_dir / "search_architecture.png")

    # Pick a canonical run directory for expression-tree / layers:
    # use depth‑4, h=32 run if present, else any matching field run.
    field_run = root / "field_n7-11-13_d4_h32_r30_bw2000"
    if not field_run.exists():
        # fall back to any field_n*_d*_h32* directory
        for p in sorted(root.glob("field_n*_d*_h32_*")):
            if p.is_dir():
                field_run = p
                break

    if args.mode in ("all", "expr-tree") and field_run.exists():
        if args.mode == "expr-tree":
            ns = [args.n]
        else:
            # In "all" mode, produce one example per target n.
            ns = [7, 11, 13]
        for n_val in ns:
            plot_expression_tree(
                field_run,
                n=n_val,
                depth_level=args.depth,
                rank=args.rank,
                out_path=out_dir
                / f"expr_tree_n{n_val}_d{args.depth}_r{args.rank}.png",
            )

    if args.mode in ("all", "heatmap"):
        plot_depth1_heatmap(
            n=args.n,
            m=args.m,
            max_height=args.max_height,
            out_path=out_dir
            / f"depth1_heatmap_n{args.n}_m{args.m}_h{args.max_height}.png",
        )

    if args.mode in ("all", "layers"):
        depth_csv = out_dir / "depth_scaling_table.csv"
        if depth_csv.exists():
            plot_tower_layers(depth_csv, n=args.n, out_path=out_dir / f"tower_layers_n{args.n}.png")


if __name__ == "__main__":
    main()

