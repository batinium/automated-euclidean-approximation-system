"""Field-first search: enumerate constructible approximations via quadratic
tower normal forms instead of syntax trees.

Instead of generating and pruning expression trees, this module represents
candidates by their coordinates in quadratic field extensions:

- Depth 0: rationals  A  (bounded height)
- Depth 1: A + B√m     for squarefree m, rational A, B
- Depth d: P + Q√(inner_{d-1})  — recursive nesting of quadratic towers

Tree building is deferred: numerical values are computed in fast float
arithmetic first, and only top candidates are materialised as ExprNode trees.
A biquadratic refinement pass (adding C√n corrections) enriches each level.
"""

from __future__ import annotations

import math
from fractions import Fraction

import mpmath

from .canonicalize import canonicalize
from .evaluate import clear_cache, evaluate
from .expr import ExprNode, Op


# ── deterministic sort key (same contract as search.py) ──────────────


def _sort_key(entry: tuple[float, ExprNode]) -> tuple[float, int, str]:
    err, expr = entry
    return (err, expr.node_count, expr.to_str())


# ── number-theoretic helpers ─────────────────────────────────────────


def _squarefree_up_to(limit: int) -> list[int]:
    """Positive squarefree integers in [2, *limit*]."""
    if limit < 2:
        return []
    is_sf = [True] * (limit + 1)
    for p in range(2, int(math.isqrt(limit)) + 1):
        p2 = p * p
        for k in range(p2, limit + 1, p2):
            is_sf[k] = False
    return [n for n in range(2, limit + 1) if is_sf[n]]


def _bounded_rationals(
    max_height: int, lo: float = -3.0, hi: float = 3.0
) -> list[Fraction]:
    """Reduced fractions p/q with 1 ≤ q ≤ *max_height* and value in [lo, hi]."""
    result: set[Fraction] = set()
    for q in range(1, max_height + 1):
        p_lo = math.ceil(lo * q)
        p_hi = math.floor(hi * q)
        for p in range(p_lo, p_hi + 1):
            result.add(Fraction(p, q))
    return sorted(result, key=float)


def _best_rational_approx(target: float, max_denom: int) -> Fraction:
    """Closest p/q to *target* with denominator ≤ *max_denom*."""
    best = Fraction(round(target))
    best_err = abs(float(best) - target)
    for q in range(1, max_denom + 1):
        p = round(target * q)
        frac = Fraction(p, q)
        err = abs(float(frac) - target)
        if err < best_err:
            best = frac
            best_err = err
    return best


# ── tree builders ────────────────────────────────────────────────────


def _make_const(v: Fraction) -> ExprNode:
    return ExprNode(Op.CONST, value=v)


def _make_depth1_tree(a: Fraction, b: Fraction, m: int) -> ExprNode:
    """Canonical tree for  a + b·√m."""
    a_node = _make_const(a)
    sqrt_m = ExprNode(Op.SQRT, children=(_make_const(Fraction(m)),))
    b_sqrt = ExprNode(Op.MUL, children=(_make_const(b), sqrt_m))
    return canonicalize(ExprNode(Op.ADD, children=(a_node, b_sqrt)))


def _make_nested_tree(
    p: Fraction, q: Fraction, inner_tree: ExprNode
) -> ExprNode:
    """Canonical tree for  p + q·√(inner_tree)."""
    sqrt_inner = ExprNode(Op.SQRT, children=(inner_tree,))
    q_sqrt = ExprNode(Op.MUL, children=(_make_const(q), sqrt_inner))
    return canonicalize(ExprNode(Op.ADD, children=(_make_const(p), q_sqrt)))


def _make_correction_tree(
    base_tree: ExprNode, c: Fraction, n: int
) -> ExprNode:
    """Canonical tree for  base_tree + c·√n  (biquadratic refinement)."""
    c_sqrt_n = ExprNode(
        Op.MUL,
        children=(
            _make_const(c),
            ExprNode(Op.SQRT, children=(_make_const(Fraction(n)),)),
        ),
    )
    return canonicalize(ExprNode(Op.ADD, children=(base_tree, c_sqrt_n)))


# ── main search ──────────────────────────────────────────────────────


def field_search(
    target: mpmath.mpf,
    n_val: int,
    max_depth: int = 3,
    max_height: int = 20,
    max_radicand: int = 30,
    max_nodes: int = 50,
    beam_width: int = 2000,
    dps: int = 80,
    seed: int = 42,
    progress: bool = False,
) -> dict[int, list[tuple[float, ExprNode]]]:
    """Field-first search for constructible approximations to cos(2π/n).

    Returns ``dict[int, list[(error, ExprNode)]]`` — same interface as
    :func:`beam_search` for drop-in compatibility.
    """
    clear_cache()
    target_f = float(target)

    squarefrees = _squarefree_up_to(max_radicand)
    with mpmath.workdps(dps + 15):
        sqrt_mpf = {m: mpmath.sqrt(m) for m in squarefrees}
    sqrt_f = {m: float(sqrt_mpf[m]) for m in squarefrees}

    results: dict[int, list[tuple[float, ExprNode]]] = {}
    cumulative: list[tuple[float, ExprNode]] = []
    seen: set[int] = set()

    def _register(tree: ExprNode) -> bool:
        h = hash(tree)
        if h in seen:
            return False
        if tree.node_count > max_nodes:
            return False
        val = evaluate(tree, dps)
        if val is None:
            return False
        fv = float(val)
        if not math.isfinite(fv):
            return False
        seen.add(h)
        cumulative.append((abs(fv - target_f), tree))
        return True

    def _prune_and_snapshot(depth: int) -> None:
        nonlocal cumulative, seen
        cumulative.sort(key=_sort_key)
        # Diversity: reserve slots per sqrt-depth level
        by_sd: dict[int, list[tuple[float, ExprNode]]] = {}
        for entry in cumulative:
            sd = entry[1].sqrt_depth
            by_sd.setdefault(sd, []).append(entry)

        per_level = max(beam_width // max(max_depth + 1, 1), 50)
        kept: list[tuple[float, ExprNode]] = []
        kept_h: set[int] = set()

        for sd in sorted(by_sd):
            for entry in by_sd[sd][:per_level]:
                h = hash(entry[1])
                if h not in kept_h:
                    kept_h.add(h)
                    kept.append(entry)

        for entry in cumulative:
            if len(kept) >= beam_width:
                break
            h = hash(entry[1])
            if h not in kept_h:
                kept_h.add(h)
                kept.append(entry)

        cumulative = kept[:beam_width]
        cumulative.sort(key=_sort_key)
        seen = set(kept_h)
        results[depth] = list(cumulative)

    rationals = _bounded_rationals(max_height, lo=-2.5, hi=2.5)
    rat_f: dict[Fraction, float] = {r: float(r) for r in rationals}

    # ═══════════════════════════════════════════════════════════════════
    #  DEPTH 0 — Rationals
    # ═══════════════════════════════════════════════════════════════════
    for a in rationals:
        _register(canonicalize(_make_const(a)))

    for md in (max_height, max_height**2):
        cf = _best_rational_approx(target_f, md)
        _register(canonicalize(_make_const(cf)))

    _prune_and_snapshot(0)
    if progress:
        _report(results, 0)
    if max_depth < 1:
        return results

    # ═══════════════════════════════════════════════════════════════════
    #  DEPTH 1 — A + B√m  (guided float pre-filter → tree build)
    # ═══════════════════════════════════════════════════════════════════

    # Phase 1: fast float scoring — millions of (A, B, m) triples
    d1_raw: list[tuple[float, Fraction, int, int, int]] = []

    for mi, m in enumerate(squarefrees):
        sv = sqrt_f[m]
        for a in rationals:
            af = rat_f[a]
            b_target = (target_f - af) / sv

            for q in range(1, max_height + 1):
                p_center = round(b_target * q)
                hw = 2 if q > 6 else 3
                for p in range(p_center - hw, p_center + hw + 1):
                    if p == 0:
                        continue
                    x = af + (p / q) * sv
                    err = abs(x - target_f)
                    d1_raw.append((err, a, p, q, mi))

    d1_raw.sort()

    # Phase 2: build trees only for top survivors
    d1_built: set[tuple[Fraction, Fraction, int]] = set()
    for err, a, p, q, mi in d1_raw[: beam_width * 5]:
        b = Fraction(p, q)
        m = squarefrees[mi]
        key = (a, b, m)
        if key in d1_built:
            continue
        d1_built.add(key)
        _register(_make_depth1_tree(a, b, m))

    # Phase 3: biquadratic refinement — add C√n correction to top surds
    pool_sd1 = [
        (err, tree) for err, tree in cumulative if tree.sqrt_depth == 1
    ]
    pool_sd1.sort(key=_sort_key)
    for err, tree in pool_sd1[: min(200, len(pool_sd1))]:
        val = evaluate(tree, dps)
        if val is None:
            continue
        residual = target_f - float(val)
        for n in squarefrees:
            c_opt = residual / sqrt_f[n]
            c = _best_rational_approx(c_opt, max_height)
            if c == Fraction(0):
                continue
            _register(_make_correction_tree(tree, c, n))

    _prune_and_snapshot(1)
    if progress:
        _report(results, 1)
    if max_depth < 2:
        return results

    # ═══════════════════════════════════════════════════════════════════
    #  DEPTH 2+ — Recursive nesting: P + Q√(inner_{d−1})
    # ═══════════════════════════════════════════════════════════════════

    for d in range(2, max_depth + 1):
        _search_nested_depth(
            d,
            target_f,
            results,
            cumulative,
            seen,
            squarefrees,
            sqrt_f,
            rationals,
            rat_f,
            max_height,
            max_nodes,
            beam_width,
            dps,
            _register,
        )

        # Biquadratic refinement of new depth-d expressions
        new_d = [
            (err, tree) for err, tree in cumulative if tree.sqrt_depth == d
        ]
        new_d.sort(key=_sort_key)
        for err, d_tree in new_d[: min(100, len(new_d))]:
            val = evaluate(d_tree, dps)
            if val is None:
                continue
            residual = target_f - float(val)
            for n in squarefrees:
                c_opt = residual / sqrt_f[n]
                c = _best_rational_approx(c_opt, max_height)
                if c == Fraction(0):
                    continue
                _register(_make_correction_tree(d_tree, c, n))

        _prune_and_snapshot(d)
        if progress:
            _report(results, d)

    return results


# ── depth d ≥ 2 nested search ────────────────────────────────────────


def _search_nested_depth(
    d: int,
    target_f: float,
    results: dict[int, list[tuple[float, ExprNode]]],
    cumulative: list[tuple[float, ExprNode]],
    seen: set[int],
    squarefrees: list[int],
    sqrt_f: dict[int, float],
    rationals: list[Fraction],
    rat_f: dict[Fraction, float],
    max_height: int,
    max_nodes: int,
    beam_width: int,
    dps: int,
    _register,
) -> None:
    """Generate depth-*d* candidates via P + Q√(inner) where inner has
    sqrt_depth = d−1 and positive value."""

    # Collect positive inner values at exactly sqrt_depth d−1
    inner_pool: list[tuple[float, ExprNode]] = []
    for err, tree in results[d - 1]:
        if tree.sqrt_depth != d - 1:
            continue
        val = evaluate(tree, dps)
        if val is None or float(val) <= 1e-12:
            continue
        inner_pool.append((float(val), tree))

    # Deduplicate by hash and cap
    seen_inner: set[int] = set()
    unique: list[tuple[float, ExprNode]] = []
    for v, tree in inner_pool:
        h = hash(tree)
        if h not in seen_inner:
            seen_inner.add(h)
            unique.append((v, tree))
    inner_pool = unique[: min(500, len(unique))]

    if not inner_pool:
        return

    # Fast float pre-filter
    q_height = min(max_height, 14)
    nested_raw: list[tuple[float, Fraction, int, int, int]] = []

    for idx, (v, _inner_tree) in enumerate(inner_pool):
        sv = math.sqrt(v)
        if sv < 1e-12:
            continue
        for p in rationals:
            pf = rat_f[p]
            q_target = (target_f - pf) / sv

            for qd in range(1, q_height + 1):
                qp_center = round(q_target * qd)
                for qp in range(qp_center - 2, qp_center + 3):
                    if qp == 0:
                        continue
                    x = pf + (qp / qd) * sv
                    err = abs(x - target_f)
                    nested_raw.append((err, p, qp, qd, idx))

    nested_raw.sort()

    built: set[tuple[Fraction, Fraction, int]] = set()
    for err, p, qp, qd, idx in nested_raw[: beam_width * 5]:
        q = Fraction(qp, qd)
        key = (p, q, idx)
        if key in built:
            continue
        built.add(key)
        _, inner_tree = inner_pool[idx]
        tree = _make_nested_tree(p, q, inner_tree)
        _register(tree)


# ── progress reporting ───────────────────────────────────────────────


def _report(results: dict, depth: int) -> None:
    pool = results.get(depth, [])
    best = pool[0][0] if pool else float("inf")
    sd_dist: dict[int, int] = {}
    for _, tree in pool:
        sd = tree.sqrt_depth
        sd_dist[sd] = sd_dist.get(sd, 0) + 1
    print(
        f"[field] depth {depth}: {len(pool)} candidates, "
        f"best_err={best:.3e}, sqrt_depths={sd_dist}",
        flush=True,
    )
