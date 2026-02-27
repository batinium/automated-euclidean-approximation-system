"""Search algorithms: baseline enumeration and beam search.

Both algorithms build constructible-number expression trees and rank
them by absolute error to a target value (typically ``cos(2*pi/n)``).
"""

from __future__ import annotations

import math
from fractions import Fraction

import mpmath

from .canonicalize import canonicalize
from .evaluate import clear_cache, evaluate
from .expr import ExprNode, Op

BINARY_OPS = (Op.ADD, Op.SUB, Op.MUL, Op.DIV)

DEFAULT_CONST_SET: list[Fraction] = [
    Fraction(0),
    Fraction(1),
    Fraction(-1),
    Fraction(1, 2),
    Fraction(2),
    Fraction(3, 2),
    Fraction(3),
    Fraction(1, 4),
    Fraction(1, 3),
    Fraction(2, 3),
    Fraction(3, 4),
    Fraction(4, 3),
    Fraction(5, 4),
]


def _sort_key(entry: tuple[float, ExprNode]) -> tuple[float, int, str]:
    """Deterministic sort key: (error, node_count, canonical string)."""
    err, expr = entry
    return (err, expr.node_count, expr.to_str())


# ------------------------------------------------------------------
# Baseline enumeration
# ------------------------------------------------------------------


def baseline_enumerate(
    target: mpmath.mpf,
    max_depth: int,
    max_nodes: int,
    const_set: list[Fraction] | None = None,
    dps: int = 80,
) -> dict[int, list[tuple[float, ExprNode]]]:
    """Exhaustive (and very limited) enumeration up to the given constraints.

    Generates all valid expressions reachable by combining seed constants
    with binary ops and sqrt, subject to *max_depth* and *max_nodes*.
    Stops early if the expression set exceeds 50 000.
    """
    if const_set is None:
        const_set = list(DEFAULT_CONST_SET)

    target_f = float(target)
    clear_cache()

    seen: set[ExprNode] = set()
    all_valid: list[ExprNode] = []
    results: dict[int, list[tuple[float, ExprNode]]] = {}

    def _add(raw: ExprNode) -> ExprNode | None:
        expr = canonicalize(raw)
        if expr in seen or expr.node_count > max_nodes or expr.sqrt_depth > max_depth:
            return None
        val = evaluate(expr, dps)
        if val is None:
            return None
        fv = float(val)
        if not math.isfinite(fv):
            return None
        seen.add(expr)
        all_valid.append(expr)
        return expr

    for c in const_set:
        _add(ExprNode(Op.CONST, value=c))

    for depth in range(max_depth + 1):
        if depth > 0:
            for e in list(all_valid):
                _add(ExprNode(Op.SQRT, children=(e,)))

        snapshot = list(all_valid)
        for e1 in snapshot:
            for e2 in snapshot:
                if e1.node_count + e2.node_count + 1 > max_nodes:
                    continue
                for op in BINARY_OPS:
                    _add(ExprNode(op, children=(e1, e2)))
            if len(all_valid) > 50_000:
                break

        scored: list[tuple[float, ExprNode]] = []
        for e in all_valid:
            if e.sqrt_depth <= depth:
                val = evaluate(e, dps)
                if val is not None:
                    scored.append((abs(float(val) - target_f), e))
        scored.sort(key=_sort_key)
        results[depth] = scored

    return results


# ------------------------------------------------------------------
# Beam search
# ------------------------------------------------------------------


def beam_search(
    target: mpmath.mpf,
    max_depth: int,
    max_nodes: int,
    beam_width: int = 2000,
    const_set: list[Fraction] | None = None,
    dps: int = 80,
    seed: int = 42,
    progress: bool = False,
) -> dict[int, list[tuple[float, ExprNode]]]:
    """Beam search with heuristic pruning and diversity across sqrt depths.

    At each sqrt-depth level the search:
      1. Injects ``sqrt(e)`` for every pool member whose depth < current.
      2. Immediately combines new sqrt expressions with seed constants and
         with each other to build compound expressions.
      3. Runs general expansion rounds combining pool members with seeds
         and with top-ranked members.
      4. Prunes with diversity: reserves a minimum number of slots per
         sqrt-depth level so that deeper expressions survive pruning.
    """
    if const_set is None:
        const_set = list(DEFAULT_CONST_SET)

    target_f = float(target)
    clear_cache()

    seen: set[ExprNode] = set()
    pool: list[tuple[float, ExprNode]] = []
    results: dict[int, list[tuple[float, ExprNode]]] = {}

    def try_add(raw: ExprNode) -> ExprNode | None:
        expr = canonicalize(raw)
        if expr in seen:
            return None
        if expr.node_count > max_nodes or expr.sqrt_depth > max_depth:
            return None
        val = evaluate(expr, dps)
        if val is None:
            return None
        fv = float(val)
        if not math.isfinite(fv) or abs(fv) > 100:
            return None
        seen.add(expr)
        pool.append((abs(fv - target_f), expr))
        return expr

    def prune_diverse() -> None:
        """Prune pool with reserved slots per sqrt-depth level.

        Compared to the original version, this uses a per-depth reservation
        that does not shrink as more sqrt-depth levels become populated.
        Each level gets at least ``beam_width // (max_depth + 1)`` slots
        (capped by the actual population), up to the overall beam_width.
        """
        pool.sort(key=_sort_key)
        by_sd: dict[int, list[tuple[float, ExprNode]]] = {}
        for entry in pool:
            d = entry[1].sqrt_depth
            by_sd.setdefault(d, []).append(entry)

        kept: list[tuple[float, ExprNode]] = []
        kept_ids: set[int] = set()

        # Per-depth reservation approximates a partitioned beam: each
        # sqrt-depth level gets its own budget, instead of sharing a
        # shrinking slice as more levels appear.
        per_level_min = max(beam_width // max(max_depth + 1, 1), 50)

        for d in sorted(by_sd):
            bucket = by_sd[d]
            reserved = min(per_level_min, len(bucket))
            for entry in bucket[:reserved]:
                eid = id(entry[1])
                if eid not in kept_ids:
                    kept.append(entry)
                    kept_ids.add(eid)

        # Fill remaining capacity with globally best entries, preserving
        # determinism while allowing good candidates from any depth to
        # participate.
        for entry in pool:
            if len(kept) >= beam_width:
                break
            eid = id(entry[1])
            if eid not in kept_ids:
                kept.append(entry)
                kept_ids.add(eid)

        pool[:] = kept[:beam_width]

    def expand(left: list[ExprNode], right: list[ExprNode]) -> None:
        """Generate all binary-op combinations between *left* and *right*."""
        for e1 in left:
            nc1 = e1.node_count
            for e2 in right:
                if nc1 + e2.node_count + 1 > max_nodes:
                    continue
                for op in (Op.ADD, Op.MUL):
                    try_add(ExprNode(op, children=(e1, e2)))
                for op in (Op.SUB, Op.DIV):
                    try_add(ExprNode(op, children=(e1, e2)))
                    try_add(ExprNode(op, children=(e2, e1)))

    # ---- seed constants ----
    seeds: list[ExprNode] = []
    for c in const_set:
        node = canonicalize(ExprNode(Op.CONST, value=c))
        seeds.append(node)
        try_add(node)

    # ---- iterative deepening by sqrt depth ----
    for depth in range(max_depth + 1):
        if depth > 0:
            # Phase 1: inject sqrt expressions
            pool.sort(key=_sort_key)
            base = [e for _, e in pool[:beam_width]]
            new_sqrts: list[ExprNode] = []
            for expr in base:
                added = try_add(ExprNode(Op.SQRT, children=(expr,)))
                if added is not None and added.sqrt_depth == depth:
                    new_sqrts.append(added)

            # Phase 2: immediately combine new sqrt exprs with seeds
            # to build compound expressions (sqrt(x)+a, sqrt(x)/b, …)
            expand(new_sqrts[:min(500, len(new_sqrts))], seeds)

            # Phase 3: combine new sqrt exprs with each other. The cap
            # scales with depth so that higher sqrt-depth levels can
            # explore more radical compositions.
            sqrt_sqrt_cap = min(80 * (1 + depth), len(new_sqrts), beam_width)
            top_sq = new_sqrts[:sqrt_sqrt_cap]
            expand(top_sq, top_sq)

            # Phase 4: combine compound sqrt-expressions with seeds
            # to build deeper expressions like (sqrt(x)+a)/b
            pool.sort(key=_sort_key)
            depth_exprs = [
                e for _, e in pool
                if e.sqrt_depth == depth and e.node_count > 2
            ][:min(200, beam_width)]
            expand(depth_exprs, seeds)

            # Phase 4b: allow compound-at-depth expressions to combine
            # with each other, e.g. (sqrt(a)+b)*(sqrt(c)+d).
            top_compound = depth_exprs[: min(100, len(depth_exprs))]
            expand(top_compound, top_compound)

        # ---- general expansion rounds ----
        if depth == 0:
            n_rounds = 3
        else:
            # Deeper levels get more composition rounds; this helps
            # deep expressions catch up with strong shallow rationals.
            n_rounds = max(3, 2 + depth // 2)
        for _ in range(n_rounds):
            pool.sort(key=_sort_key)
            pool_exprs = [e for _, e in pool[:beam_width]]
            base_top_n = 100 + 50 * depth
            top_n = min(base_top_n, len(pool_exprs), beam_width)

            expand(pool_exprs, seeds)

            # Ensure sqrt-containing expressions participate in cross-products
            if depth > 0:
                sqrt_cap = min(80 * (1 + depth), beam_width)
                sqrt_pool = [
                    e for _, e in pool if e.sqrt_depth > 0
                ][:sqrt_cap]
                cross = pool_exprs[:top_n] + [
                    e for e in sqrt_pool if e not in set(pool_exprs[:top_n])
                ]
                expand(cross[:top_n], cross[:top_n])
            else:
                expand(pool_exprs[:top_n], pool_exprs[:top_n])

            prune_diverse()

        pool.sort(key=_sort_key)
        results[depth] = list(pool)

        if progress:
            best_err = pool[0][0] if pool else float("inf")
            print(
                f"[beam] depth {depth}/{max_depth} "
                f"pool={len(pool)} seen={len(seen)} best_err={best_err:.3e}",
                flush=True,
            )

    return results
