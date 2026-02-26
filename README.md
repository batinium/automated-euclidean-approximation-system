# Automated Euclidean Approximation System (AEAS)

A Python prototype that searches quadratic-radical expression trees to
approximate `cos(2π/n)` for values of *n* whose associated regular polygon
is **not** ruler-and-compass constructible (e.g. *n = 7, 11, 13*).

The system generates **constructible-number candidates** — values built from
`0` and `1` using `+, −, ×, ÷, √` — under bounded sqrt-depth and node
count, evaluates them with arbitrary precision (via `mpmath`), and reports
the best approximations.

---

## Quick start

```bash
# 1. Create and activate the environment
micromamba create -f aeas-env.yml
micromamba activate aeas

# 2. Install the package in editable mode
pip install -e .

# 3. Run the search (beam search, n=7,11,13, depth up to 3)
python scripts/run_search.py --n 7 11 13 --max_depth 3 --max_nodes 15 --beam_width 2000

# 4. Generate plots
python scripts/plot_results.py

# 5. Run the test suite
pytest tests/ -v
```

---

## Project layout

```
├── aeas-env.yml              Micromamba environment spec
├── pyproject.toml             Package metadata & build config
├── src/aeas/
│   ├── expr.py                Immutable expression-tree nodes (ExprNode, Op)
│   ├── canonicalize.py        Canonicalization, constant folding, identities
│   ├── evaluate.py            Arbitrary-precision evaluation (mpmath)
│   └── search.py              Beam search & baseline enumeration
├── scripts/
│   ├── run_search.py          CLI entry point
│   └── plot_results.py        Matplotlib visualisations
├── tests/                     pytest suite
├── data/                      (placeholder for input data)
└── results/                   JSONL, CSV, and figures saved here
```

---

## How it works

### Expression representation

Every candidate is an **immutable tree** (`ExprNode`) whose nodes are one of:

| Op | Arity | Description |
|----|-------|-------------|
| `CONST` | 0 | Rational constant (stored as `fractions.Fraction`) |
| `ADD` | 2 | Addition |
| `SUB` | 2 | Subtraction |
| `MUL` | 2 | Multiplication |
| `DIV` | 2 | Division |
| `SQRT` | 1 | Square root |

Two key metrics are tracked on each node:

- **sqrt_depth** — maximum nesting level of `SQRT` operations (0 for pure
  rationals).
- **node_count** — total number of nodes in the tree.

Hashing is structural and memoised, making deduplication via `set` O(1)
amortised.

### Canonicalization

Before an expression enters the search pool it is **canonicalized**:

1. **Recursive descent** — children are canonicalized first.
2. **Constant folding** — if all children are rational constants the expression
   is evaluated exactly with `fractions.Fraction` (division by zero and
   irrational sqrt are left symbolic).
3. **Identity elimination** — `x + 0 → x`, `x * 1 → x`, `x * 0 → 0`,
   `x / 1 → x`, `x − 0 → x`.
4. **Commutative sorting** — children of `ADD` and `MUL` are sorted by their
   canonical string representation so that `a + b` and `b + a` collapse to the
   same canonical form.

### Search strategies

**Baseline enumeration** (`--mode baseline`) — exhaustive generation of all
valid expressions up to the node/depth budget. Very slow; useful only for
tiny limits.

**Beam search** (`--mode beam`, default) — iterative deepening by sqrt-depth:

1. Seed the pool with rational constants.
2. At each depth level *d*:
   - If *d > 0*, inject `sqrt(e)` for every pool member *e*.
   - Run several expansion rounds: combine pool members with seed constants
     and with the top-ranked pool members via all binary ops.
   - Prune to `beam_width`, ranked by `(|error|, node_count, canonical_string)`.
3. Record top results per depth level.

**Heuristic filters during beam search:**

- Reject expressions that evaluate to `NaN`, `±∞`, or `|value| > 100`.
- Use a deterministic sort key for pruning to guarantee reproducibility.
- Cache evaluations to avoid redundant mpmath work.

### Evaluation

All numeric evaluation uses `mpmath` at a configurable precision (`--dps`,
default 80 decimal places) with 15 extra guard digits internally. Results are
cached by `(expression_hash, dps)` for efficiency.

### Output

| File | Contents |
|------|----------|
| `results/search_n{N}.jsonl` | Per-depth top-K results with metadata |
| `results/summary.csv` | One-row-per-(n, depth) best results |
| `results/figures/*.png` | Error-vs-depth and error-vs-nodes plots |

---

## Configuration reference

| Flag | Default | Description |
|------|---------|-------------|
| `--n` | `7 11 13` | Target polygon side counts |
| `--max_depth` | `3` | Max sqrt nesting |
| `--max_nodes` | `15` | Max tree nodes |
| `--beam_width` | `2000` | Beam width |
| `--dps` | `80` | mpmath decimal places |
| `--seed` | `42` | Seed (metadata — search is deterministic) |
| `--mode` | `beam` | `beam` or `baseline` |
| `--const_set` | `0,1,-1,1/2,2,3/2,3,1/4,1/3` | Seed rationals |
| `--top_k` | `10` | Results printed per depth |

---

## Design choices & limitations

- **Constructibility only** — the system produces values in the *constructible
  reals* (iterated square roots over ℚ). For *n = 7, 11, 13* the exact cosine
  is **not** constructible, so we report *approximations*.
- **Greedy pruning** — beam search may discard useful intermediates that would
  combine into better expressions at higher depth. Increasing `--beam_width`
  mitigates this at the cost of runtime.
- **No algebraic simplification** — we do not simplify `sqrt(sqrt(x))` to
  `x^(1/4)` or apply distributive laws. Structure is preserved as-is.
- **Hash collisions** — theoretically possible but negligible in practice with
  Python's 64-bit hash.
- **Determinism** — given the same parameters, the search always produces the
  same results (no randomness in expansion or pruning).
