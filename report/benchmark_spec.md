# CANB — Constructible Approximation Number Benchmark

**Version:** 0.1 (draft)
**Status:** proposed; not yet frozen.
**License target:** CC-BY-4.0 for data, Apache-2.0 for harness code.

---

## 1. Purpose

Standardized benchmark for methods that search for compact, low-error, bounded-height algebraic expressions (especially constructible — sums, differences, products, quotients, and nested square roots of rationals) approximating a given real target.

---

## 2. Task definition

A task is a JSON file:

```json
{
  "id": "canb-poly-n7",
  "family": "canb-poly",
  "target_description": "cos(2*pi/7)",
  "target_spec": {
    "kind": "cos_of_rational_pi",
    "arg": [2, 7]
  },
  "reference_value_dps": 1000,
  "reference_value": "0.623489801...(1000 digits)",
  "known_closed_form": null,
  "difficulty_tier": 2,
  "notes": "non-Gauss-Wantzel heptagon"
}
```

- `id` — stable string, unique in benchmark.
- `family` — one of `canb-poly`, `canb-algdeg`, `canb-nestedref`, `canb-transcend`, `canb-trig`, `canb-rand`.
- `target_spec` — structured description so tasks are re-generatable. Supported `kind`:
  - `cos_of_rational_pi`: arg = `[p, q]`, target = `cos(p·π/q)`.
  - `sin_of_rational_pi`: same.
  - `root_of_polynomial`: `coefficients` (list of integers, leading first) + `real_root_index`.
  - `literal_transcendental`: `name ∈ {pi, e, ln2, euler_gamma, apery}`.
  - `ramanujan_radical`: `expression` string in a restricted grammar (literal reference value).
  - `random_algebraic`: seed + degree + conductor bounds for reproducible sampling.
- `reference_value` — 1000-digit decimal. Canonical reference. Harness uses this for scoring.
- `difficulty_tier ∈ {1, 2, 3, 4}` — see §3.

Tasks live in `benchmark/tasks/<family>/<id>.json`.

---

## 3. Difficulty tiers

Calibration is empirical — assigned after baseline sweeps. Initial definitions:

- **Tier 1 (easy).** Reference method achieves `error < 1e-6` at `depth ≤ 1, H ≤ 16` within 10s.
- **Tier 2 (medium).** Requires `depth ≤ 2, H ≤ 32` within 60s.
- **Tier 3 (hard).** Requires `depth ≥ 3` or `H ≥ 64`.
- **Tier 4 (open).** No known method achieves `error < 1e-8` within 600s. Useful as open challenges.

Tiers are not prescribed difficulties — they are observed. Re-calibrated each benchmark version.

---

## 4. Submission format

A submission is a JSON file, one per task per method:

```json
{
  "task_id": "canb-poly-n7",
  "method": "aeas-v0.3",
  "submitted_at": "2026-04-20T12:34:56Z",
  "budget": {
    "max_walltime_sec": 60,
    "max_memory_mb": 2048,
    "max_evaluations": null
  },
  "metrics": {
    "walltime_sec": 42.1,
    "peak_memory_mb": 510,
    "num_evaluations": 185420
  },
  "expression": {
    "format": "aeas-ast-v1",
    "ast": {"op": "ADD", "args": [{"op": "CONST", "value": "1/2"}, ...]}
  },
  "error_selfreport_dps80": "4.17e-6",
  "notes": "..."
}
```

The harness re-evaluates `expression.ast` at 1000 dps and computes the canonical `error`, overriding `error_selfreport_dps80`. Self-reported error is sanity signal only.

AST grammar (`aeas-ast-v1`):

```
Node := { "op": "CONST", "value": "<rational_string>" }
      | { "op": "NEG"   , "args": [Node] }
      | { "op": "INV"   , "args": [Node] }
      | { "op": "SQRT"  , "args": [Node] }
      | { "op": "ADD"   , "args": [Node, Node] }
      | { "op": "SUB"   , "args": [Node, Node] }
      | { "op": "MUL"   , "args": [Node, Node] }
      | { "op": "DIV"   , "args": [Node, Node] }
```

Rationals serialized as `"p/q"` or `"n"`. Irrationals only via `SQRT`.

Methods may submit `"expression": null` with `"status": "timeout" | "failed"` on tasks they cannot solve; these count as worst-case scores.

---

## 5. Scoring

Per task `t`, per submission `s`:

- `e_t(s) = |eval_1000dps(s.expression) − reference_value_t|`, clamped below to `1e-100`.
- `k_t(s) = node_count(canonicalize(s.expression))`.
- `w_t(s) = min(s.metrics.walltime_sec, budget.max_walltime_sec)`.

Reference box `B` in log-space:

- `log10 e ∈ [−30, 0]`
- `log10 k ∈ [0, 3]`
- `log10 w ∈ [−3, 3]` (walltime in seconds)

Map to `[0, 1]^3` with 1 = best. Failed/timeout submissions = `(0, 0, 0)`.

Per-task Pareto hypervolume `HV_t(M)` relative to origin.

**Primary score** for method `M` on split `S`:

```
Score(M, S) = mean over t ∈ S of HV_t(M)
```

**Secondary scores:**

- `BestError(M, S) = median_t log10 e_t(s_best)`
- `WinRate(M, S, budget) = fraction of tasks where M's error at given budget is lowest`
- `ExactRate(M, S) = fraction of tasks where e_t < 1e-20` (treated as algebraic coincidence)
- `SizeAtBest(M, S) = median_t k_t(s_best)`

**Leaderboard** sorts by `Score`; ties broken by `ExactRate` then `BestError`.

---

## 6. Splits

`canb-poly`, `canb-algdeg`, `canb-nestedref`, `canb-transcend`, `canb-trig`, `canb-rand`.

Each split further partitioned `train` / `dev` / `test` 70/15/15 by `id` hash, so methods with hyperparameters cannot overfit. `test` locked; `dev` open for method tuning.

---

## 7. Task generation (reproducibility)

`scripts/generate_benchmark.py --split canb-poly --version 0.1 --seed 20260420`

Must regenerate byte-identical `benchmark/tasks/` from seed + version. Generator writes `benchmark/MANIFEST.json` listing every task + SHA256.

Reference values computed with `mpmath` at 1100 dps, truncated to 1000. Written as decimal strings (not floats) to avoid serialization drift.

---

## 8. Submission protocol for the public leaderboard

- Method author opens PR adding `benchmark/submissions/<method-name>/<version>/*.json` + method description markdown.
- CI re-runs scoring on `test` split; posts scores.
- Reproducibility clause: submitters must link to source code or binary. If no code, flagged `unreproduced` on leaderboard.

---

## 9. Ethical / scope notes

- No sensitive data. Purely mathematical.
- LLM-based submissions allowed but tagged `llm-*`; leaderboard can filter.
- Methods using test-set reference values in prompts → disqualified.

---

## 10. Versioning policy

- `v0.x`: pre-release, task set may change.
- `v1.0`: freeze; no changes except additive new splits.
- Breaking changes → `v2.0`, both versions scored in parallel for one cycle.
