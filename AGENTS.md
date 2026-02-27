# AGENTS.md — AI Agent Guide for AEAS

## What this project is

**Automated Euclidean Approximation System (AEAS)** — a Python prototype
that searches constructible-number approximations to `cos(2π/n)` for
non-constructible polygon side counts (n = 7, 11, 13, …).

The system has two search backends:
- **Tree-based** (`beam_search`, `baseline_enumerate`) — enumerates expression
  trees built from `{0,1}` with `+, −, ×, ÷, √`.
- **Field-first** (`field_search`) — enumerates elements by their coordinates
  in quadratic field towers (normal forms), then materialises ExprNode trees
  only for top candidates.  This avoids the exponential redundancy of tree
  enumeration and eliminates beam collapse at higher sqrt depths.

Both backends evaluate candidates at arbitrary precision via `mpmath` and
report the best approximations.

## Repository layout

```
.
├── pyproject.toml            # Package metadata, dependencies, build config
├── aeas-env.yml              # Micromamba/conda environment specification
├── conftest.py               # Root pytest hook — adds src/ to sys.path
├── src/aeas/                 # Main library package (installed as `aeas`)
│   ├── __init__.py           # Re-exports: ExprNode, Op, canonicalize, evaluate, …
│   ├── expr.py               # ExprNode (immutable tree node) + Op enum
│   ├── canonicalize.py       # Canonicalization, constant folding, identity elim.
│   ├── evaluate.py           # mpmath evaluation with global result cache
│   ├── search.py             # beam_search() and baseline_enumerate()
│   ├── chebyshev.py          # Chebyshev polynomial T_n evaluation and residual
│   └── field_search.py       # field_search() — normal-form quadratic-tower search
├── scripts/
│   ├── run_search.py         # CLI entry point (argparse + rich output)
│   └── plot_results.py       # Reads results/ JSONL → matplotlib PNGs
├── tests/
│   ├── test_expr.py          # ExprNode construction, depth, hashing, immutability
│   ├── test_evaluate.py      # Evaluation correctness, safety checks, targets
│   ├── test_canonicalize.py  # Folding, identities, idempotence, hash stability
│   ├── test_chebyshev.py     # T_n identity, float/mpmath agreement, residuals
│   └── test_field_search.py  # Utilities, tree builders, search quality, format
├── data/                     # Placeholder for input data
└── results/                  # Output directory (JSONL, CSV, figures/)
```

## Environment & installation

```bash
micromamba create -f aeas-env.yml && micromamba activate aeas
pip install -e ".[dev]"       # editable install with pytest + sympy
```

Python ≥ 3.11. Key runtime deps: `mpmath`, `numpy`, `matplotlib`, `pandas`,
`rich`. Dev deps: `pytest`, `sympy`.

## Running

```bash
# Field-first search (recommended, ~80s per n value)
python scripts/run_search.py --mode field --n 7 11 13 --max_depth 3 --progress

# Tree-based beam search (legacy, ~30s per n value)
python scripts/run_search.py --n 7 11 13 --max_depth 3 --max_nodes 15 --beam_width 2000

# Baseline (exhaustive, very slow for large limits)
python scripts/run_search.py --mode baseline --max_depth 1 --max_nodes 7

# Each invocation creates a dedicated run directory under results/,
# e.g. results/n7-11-13_d3_nodes15_beam2000_YYYYMMDD-HHMMSS/

# Generate plots for the latest run (or pass --run <name> explicitly)
python scripts/plot_results.py
python scripts/plot_results.py --run n7-11-13_d3_nodes15_beam2000_YYYYMMDD-HHMMSS

# Tests (101 tests across 5 files)
pytest tests/ -v
```

### CLI flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--n` | `7 11 13` | Target polygon side counts |
| `--max_depth` | `3` | Max sqrt nesting depth |
| `--max_nodes` | `15` | Max tree node count (auto ≥50 for field mode) |
| `--beam_width` | `2000` | Candidates retained per round |
| `--dps` | `80` | mpmath decimal places |
| `--seed` | `42` | Metadata only (search is deterministic) |
| `--mode` | `beam` | `beam`, `baseline`, or `field` |
| `--const_set` | `0,1,-1,1/2,2,3/2,3,1/4,1/3` | Seed rationals (beam/baseline) |
| `--max_height` | `20` | Max numerator/denominator for coefficients (field) |
| `--max_radicand` | `30` | Largest squarefree radicand to search (field) |
| `--top_k` | `10` | Results displayed per depth level |
| `--output_root` | `results` | Parent directory for all runs |
| `--run_name` | *auto* | Optional explicit run subdirectory name |

`scripts/plot_results.py` CLI:

| Flag | Default | Purpose |
|------|---------|---------|
| `--root` | `results` | Root containing run subdirectories |
| `--run` | latest run | Run folder under `--root` to plot |
| `--all-runs` | False | Generate figures for **every** run folder under `--root` that contains `search_n*.jsonl` |

## Architecture & core concepts

### ExprNode (`src/aeas/expr.py`)

Immutable expression-tree node. Uses `__slots__` and bypasses `__setattr__`
via `object.__setattr__` in `__init__` for true immutability.

Key properties (lazily computed, memoised):
- `sqrt_depth` — max SQRT nesting (CONST=0, SQRT(x)=x.sqrt_depth+1, binary=max of children).
- `node_count` — total nodes (1 + sum of children).
- `to_str()` — deterministic parenthesised infix string, also memoised.

Hashing is structural: `hash((op, children))` for non-CONST,
`hash((Op.CONST, value))` for constants. `__eq__` checks structural equality.
This means two independently-constructed trees with identical shape and leaves
compare equal and share the same hash.

**Op enum values:** `CONST` (arity 0, leaf — `value` is `fractions.Fraction`),
`ADD`, `SUB`, `MUL`, `DIV` (arity 2), `SQRT` (arity 1).

### Canonicalization (`src/aeas/canonicalize.py`)

`canonicalize(node)` → canonical ExprNode. Applied before every pool insertion.

Pipeline (recursive, children-first):
1. **Constant folding** — both children are CONST → exact `Fraction` arithmetic.
   For SQRT: only folds perfect-square rationals; irrational results kept symbolic.
   Division by zero → returns `None` (expression kept as-is, rejected at eval).
2. **Identity elimination** — `x+0→x`, `x−0→x`, `x*1→x`, `x*0→0`, `x/1→x`,
   `sqrt(0)→0`, `sqrt(1)→1`.
3. **Commutative sorting** — ADD and MUL children sorted by `to_str()` so
   `a+b` and `b+a` produce identical canonical trees.

**Important consequence:** all pure-rational sub-expressions collapse into
single CONST nodes. E.g. `ADD(CONST(1), CONST(2))` → `CONST(3)`. This means
the depth-0 beam is populated entirely by 1-node rational constants.

### Evaluation (`src/aeas/evaluate.py`)

`evaluate(node, dps=80)` → `mpmath.mpf | None`.

- Uses `mpmath.workdps(dps + 15)` for guard digits.
- Module-level `_cache: dict[(hash, dps), mpf | None]` avoids redundant
  sub-expression evaluation. Call `clear_cache()` between independent searches
  or test runs.
- Returns `None` for: division by zero, sqrt of negative, non-finite result.

`compute_target(n, dps)` → `cos(2π/n)` at given precision.

### Chebyshev module (`src/aeas/chebyshev.py`)

Provides `chebyshev_T(n, x, dps)` and a fast float variant `chebyshev_T_float`.
For target α = cos(2π/n), the identity T_n(α) = 1 gives a structurally
meaningful error signal via `chebyshev_residual(n, x)` = |T_n(x) − 1|.

### Field-first search (`src/aeas/field_search.py`) — **recommended**

`field_search(target, n_val, max_depth, max_height, max_radicand, …)`

The core insight: every constructible number of sqrt-depth d lives in a
quadratic field tower Q ⊂ Q(√a₁) ⊂ Q(√a₁, √(b+c√a₁)) ⊂ … of degree
dividing 2^d.  Instead of enumerating syntax trees (exponential redundancy),
the field search enumerates **normal-form coordinates** in these towers:

- **Depth 0** — rationals A with bounded height, plus continued-fraction
  best-approximation with larger denominator.
- **Depth 1** — A + B√m for squarefree m ≤ max_radicand.  Uses guided
  coefficient search: for each (A, m), compute B_opt = (α−A)/√m, then
  search nearby rationals.  Followed by **biquadratic refinement**: add
  C√n correction to top depth-1 results.
- **Depth d ≥ 2** — P + Q√(inner_{d−1}) where inner is a positive-valued
  depth-(d−1) expression from the previous level.  Same guided coefficient
  search for (P, Q).  Followed by biquadratic refinement at each level.

**Two-phase architecture** for each depth:
1. **Float pre-filter** — evaluate millions of (coefficient, radicand) tuples
   using fast float arithmetic.  Sort by error, take top N.
2. **Tree materialisation** — build canonical ExprNode trees and evaluate with
   mpmath only for the top survivors.

**Diversity-preserving pruning** across sqrt-depth levels ensures deeper
candidates survive so they can serve as inner values for the next tower level.

### Tree-based search (`src/aeas/search.py`) — legacy

Two algorithms share the same return type:
`dict[int, list[tuple[float, ExprNode]]]` — depth → sorted list of
`(absolute_error, expression)`.

**`baseline_enumerate`** — BFS-style exhaustive generation. Caps at 50K
expressions. Only useful for tiny limits (`max_nodes ≤ 7`, `max_depth ≤ 1`).

**`beam_search`** — tree-enumeration beam search. Per sqrt-depth level:
1. **Sqrt injection** — `sqrt(e)` for each pool member.
2. **Immediate expansion** — new sqrt expressions × seed constants.
3. **General expansion** — pool × seeds, then top-N × top-N cross-product.
4. **Diversity-aware pruning** — reserves slots per sqrt-depth level.

Sort key everywhere: `(error, node_count, canonical_string)` — fully deterministic.

### Scripts

`scripts/run_search.py` — parses CLI args, determines a **run directory**
under `results/` (either from `--run_name` or from the parameter set +
timestamp), writes:

- `run_config.json` — full configuration for the run (all CLI args, run_name,
  timestamp, paths).
- `search_n{N}.jsonl` — per-depth top-K results for each n.
- `summary.csv` — one-row-per-(n, depth) best results.

It also prints rich tables and a sub-table for best results at each exact
sqrt-depth.

`scripts/plot_results.py` — chooses a run directory (explicit `--run` or the
most recent subdirectory under `--root` with `search_n*.jsonl`) and generates
three matplotlib figures in `<run>/figures/`. With `--all-runs` it iterates
over **all** such run directories under `--root` and regenerates figures for
each:

- `error_vs_depth.png` — semilogy best error vs sqrt depth, one subplot per n.
- `error_vs_nodes.png` — scatter of error vs node count.
- `combined_errors.png` — all n values on one axes.

## Testing

101 tests across 5 files. Run with `pytest tests/ -v`.

| File | What it covers |
|------|---------------|
| `test_expr.py` | sqrt_depth, node_count, hashing/equality, immutability, to_str |
| `test_evaluate.py` | basic ops, sqrt, div-by-zero, sqrt-negative, nested invalids, compute_target |
| `test_canonicalize.py` | commutative sorting, constant folding (incl. perfect-square sqrt), all identity rules, idempotence, hash consistency |
| `test_chebyshev.py` | T_n recurrence, T_n(cos(2π/n))=1 identity, float/mpmath agreement, residuals |
| `test_field_search.py` | squarefree generation, bounded rationals, best rational approx, tree builders (depth 1/2/correction), search format, quality (monotone improvement with depth), determinism |

Each evaluate and field_search test auto-clears the eval cache via an `autouse` fixture.

## Key invariants an agent must preserve

1. **ExprNode immutability** — never add `__setattr__` that allows mutation.
   All cached properties use `object.__setattr__` in controlled paths only.
2. **Canonicalize-before-insert** — every expression entering the search pool
   must pass through `canonicalize()`. Skipping this breaks deduplication.
3. **Eval cache coherence** — `clear_cache()` must be called between
   independent searches (both algorithms do this at the top). If you add a
   new search function, call it first.
4. **`_sort_key` determinism** — the sort key `(error, node_count, to_str())`
   ensures reproducible beam pruning. Do not introduce randomness or
   non-deterministic ordering.
5. **Safety rejects** — `evaluate()` returns `None` for div-by-zero and
   sqrt-of-negative. The search loop must filter these. Never silently
   substitute a default (like `abs(x)` for negative sqrt).
6. **Constant folding boundary** — only fold when ALL children are CONST.
   Partial folding (e.g. `CONST+non-CONST`) is not performed; this is by design.
7. **Results structure** — all three search functions return
   `dict[int, list[tuple[float, ExprNode]]]`. The CLI and plot scripts
   depend on this shape and on the JSONL field names
   (`n, depth, nodes, sqrt_depth, best_error, expression, runtime, seed, dps, rank`).
8. **Field search two-phase invariant** — float pre-filtering must precede
   tree materialisation.  Never build ExprNode trees for all candidates; only
   materialise the top `beam_width * N` survivors from the float scoring phase.

## Common modification patterns

### Adding a new operation (e.g. NEG, POW2)

1. Add variant to `Op` enum in `expr.py`.
2. Handle it in `ExprNode._build_str()`, `sqrt_depth`, `node_count`.
3. Add folding/simplification cases in `canonicalize.py`.
4. Add evaluation case in `evaluate.py` `_eval()`.
5. Add generation logic in `search.py` (both algorithms).
6. Add tests for the new op in all three test files.

### Changing the seed constant set

Pass `--const_set` on the CLI. In code, modify `DEFAULT_CONST_SET` in
`search.py`. Constants are `fractions.Fraction` values. After constant folding,
any rational reachable by combining seeds with `+−×÷` becomes a single CONST
node.

### Tuning field search performance

- Increase `--max_height` for finer rational coefficients (quadratic cost).
- Increase `--max_radicand` to search more number fields (linear cost).
- Increase `--beam_width` to keep more candidates per level (linear cost).
- The B-coefficient search window is `p_center ± hw` where hw=3 for small
  denominators (q ≤ 6) and hw=2 for larger.  Widening improves quality but
  increases the float pre-filter set.
- The biquadratic refinement takes top 200 surds and tries C√n corrections
  with all radicands — cap adjustable in `field_search()`.

### Tuning beam search performance (legacy)

- Increase `--beam_width` for better results (linear cost increase).
- Increase `--max_nodes` to allow more complex expressions (combinatorial cost).
- The diversity reservation in `prune_diverse()` is
  `beam_width // (3 * n_levels)` — adjust the `3` divisor to trade diversity
  for exploitation.
- Expansion limits: `500` for sqrt×seeds, `80` for sqrt×sqrt, `200` for
  compound×seeds, `100` for top-N cross-product. These are in `beam_search()`
  and can be tuned.

### Adding output formats

JSONL and CSV writers are in `scripts/run_search.py`. The JSONL schema is one
JSON object per line with the fields listed in "Key invariants" above. Plot
readers in `scripts/plot_results.py` use `pd.DataFrame(records)` and group by
`n` and `depth`.

## Mathematical context

A regular n-gon is ruler-and-compass constructible iff n is a product of a
power of 2 and distinct Fermat primes (3, 5, 17, 257, 65537). For n = 7, 11,
13 the exact `cos(2π/n)` is **not** a constructible number. This system
searches the constructible reals — the smallest field closed under `√` over
Q — for the best approximations.

The search is structured by **sqrt-depth**: depth 0 = rationals,
depth 1 = expressions using one level of `√`, depth 2 = nested `√(… √(…) …)`,
etc. Higher depth = richer number field, potentially better approximations.

Observed error magnitudes — field search (max_height=20, max_radicand=30,
beam_width=2000):

| n  | depth 0 | depth 1 | depth 2 | depth 3 |
|----|---------|---------|---------|---------|
| 7  | ~10⁻⁶  | ~10⁻⁷  | ~10⁻⁹  | ~10⁻¹⁰ |

Observed error magnitudes — beam search (beam_width=2000, max_nodes=15):

| n  | depth 0 | depth 1 | depth 2 |
|----|---------|---------|---------|
| 7  | ~10⁻⁴  | ~10⁻⁷  | ~10⁻⁸  |
| 11 | ~10⁻⁵  | ~10⁻⁶  | ~10⁻⁸  |
| 13 | ~10⁻⁵  | ~10⁻⁶  | ~10⁻⁸  |
