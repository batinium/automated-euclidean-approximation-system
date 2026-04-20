# AEAS — Track A Reframing Plan (Benchmark + Method Paper)

**Status:** active planning doc. Supersedes `archive/PLAN_v1.md`.
**Date started:** 2026-04-20.
**One-line pitch:** *CANB: Constructible Approximation Number Benchmark — a public benchmark + reference method (AEAS) for bounded-height algebraic approximation in explicit quadratic towers.*

---

## 1. Why Track A (benchmark reframing)

Prior submissions were rejected for specificity (hand-crafted tridecagon construction). Track A generalizes the target set from `{cos(2π/7), cos(2π/11), cos(2π/13)}` to a public benchmark of algebraic-number approximation tasks, positioning AEAS as the reference method. This:

- Converts "too specific" into "defined a new evaluation regime."
- Forces external baselines (PSLQ, LLL, PySR, continued fractions) as first-class submissions, fixing the in-house-only baseline critique.
- Unlocks NeurIPS D&B / AAAI datasets / ACM TOMS / Math. Comp. venue pools in addition to the original symbolic-computation pool.
- Reuses ~90% of existing AEAS implementation. Core code does not change; the paper narrative and evaluation harness do.

The tridecagon / cos(2π/n) story becomes an illustrative subset (CANB-Poly), not the headline.

---

## 2. Paper contributions (new)

1. **CANB benchmark.** Public benchmark of ~300–1000 algebraic-number approximation tasks with a well-defined task schema, scoring, splits, and leaderboard protocol. First such benchmark in this area.
2. **Scoring formalism.** Error–height–depth–walltime Pareto scoring with a single scalar aggregate (explained in §7) so leaderboard ordering is well-defined while still exposing the full frontier.
3. **Reference method.** AEAS as a reference baseline: field-first normal-form search over quadratic towers with float pre-filter + delayed symbolic materialization + diversity-preserving pruning.
4. **Baseline suite.** External baselines wired into the harness: (a) continued fractions, (b) PSLQ/LLL integer-relation detection over tower bases, (c) tree-GP (PySR or gplearn), (d) MCTS over an expression grammar, (e) brute-force enumeration up to a bound (sanity reference at small depth).
5. **Empirical findings.** Frontier analysis across task families showing (i) field-first Pareto dominance in structured-target regimes, (ii) PSLQ wins when an exact algebraic relation exists, (iii) depth-vs-height scaling laws per target family.
6. **Theoretical result.** Completeness at depth 1 under stated bounds + complexity per stage.

---

## 3. Benchmark design (CANB)

Full spec in `report/benchmark_spec.md`. Summary:

### 3.1 Task families (splits)

| Split | Targets | Size (planned) |
|---|---|---|
| `CANB-Poly` | `cos(2π/n)` for non-Gauss-Wantzel `n ∈ [7, 200]` | ~60 |
| `CANB-AlgDeg` | Roots of random irreducible polynomials of degrees 2–8 | ~200 |
| `CANB-NestedRef` | Targets with known closed-form nested radicals (Ramanujan-style, reference points for upper bounds) | ~40 |
| `CANB-Transcend` | Transcendentals (π, e, ln 2, γ, ζ(3)) — control set where no exact algebraic solution exists | ~10 |
| `CANB-Trig` | `sin(p/q · π)`, `tan(p/q · π)` for small rationals with non-constructible `q` | ~50 |
| `CANB-Rand` | Sampled algebraic numbers in `[-1, 1]` with controlled degree + conductor | ~200 |

Each task = JSON with `id`, `target_description`, `target_mpmath_expression`, `reference_value_1000dps`, `known_closed_form` (optional), `difficulty_tier`.

### 3.2 Submission interface

- Input: a task JSON + compute budget (`max_walltime_sec`, `max_memory_mb`, `max_evaluations`).
- Output: an expression in a canonical AST schema (same as AEAS's `expr.py`), plus evaluation metadata.
- Harness evaluates the expression at 1000 dps via `mpmath`, computes absolute error, records walltime + memory.
- Submissions may be partial (some tasks unsolved).

### 3.3 Scoring

Primary metric: **Pareto-hypervolume** in `(log10 error, log10 expression_size, log10 walltime)` space per task, normalized and averaged over the split. Secondary: per-task win rate at matched compute.

Also report:
- `error @ budget=60s`
- `best error regardless of budget`
- `expression size at best error`
- `PSLQ-detected algebraic coincidence rate` (for methods that hit zero within tolerance).

### 3.4 Difficulty tiers

Tier 1: depth ≤ 1 suffices for `error < 10^-6` with `H ≤ 16`.
Tier 2: depth ≤ 2, `H ≤ 32`.
Tier 3: depth ≥ 3 or `H ≥ 64` required.
Tier 4: no known closed-form constructible expression beats `H = 32, d = 4`.

---

## 4. Experimental plan

### Phase 0 — Rewrite paper skeleton (1 day)
Already done: `report/aeas_paper.tex` new skeleton. See §10 for detail.

### Phase 1 — Benchmark harness (1–2 weeks)
1. Define task JSON schema — see `benchmark_spec.md`.
2. Script `scripts/generate_benchmark.py` — emit task files for all splits into `benchmark/tasks/*.json`.
3. Script `scripts/run_benchmark.py` — invoke a method over a task set, collect submissions into `benchmark/submissions/<method>/<task_id>.json`.
4. Script `scripts/score_benchmark.py` — compute Pareto hypervolume + secondary metrics, emit `benchmark/scores/<method>.csv`.
5. Adapt AEAS so it emits a standard submission file.
6. Adapt run_search.py to be a `method` under the harness (backward-compatible wrapper).

Deliverable: `python scripts/run_benchmark.py --method aeas --split canb-poly` produces valid submissions + scored results end-to-end.

### Phase 2 — Baseline implementations (2–3 weeks)

Each baseline = one file under `src/aeas/baselines/<name>.py` with a `solve(task, budget)` function returning a submission.

| Baseline | Library | Notes |
|---|---|---|
| Continued fractions | stdlib + `fractions` | depth-0 sanity floor |
| PSLQ | `mpmath.pslq` | basis `{1, sqrt(m_1), ..., prod(sqrt(m_i))}` up to chosen depth |
| LLL | `fpylll` | reduce candidate lattice of tower basis coefficients |
| Tree-GP | `gplearn` or **PySR** | operators `{+,-,*,/,sqrt}` only, seeded with rationals |
| MCTS | custom | Kamienny-style over expression grammar |
| Brute-force enum | custom | exhaustive to depth ≤ 2, bounded height, sanity reference |
| LLM (optional) | Anthropic SDK | `claude-opus-4-7` given task + budget, outputs canonical AST. Strong reviewer signal. |

Deliverable: all six baselines submit non-empty results on CANB-Poly within 60s/task budget.

### Phase 3 — Matched-compute evaluation (1 week)

- Sweep walltime budgets `{1, 10, 60, 600} sec` per task.
- Sweep memory caps `{512MB, 2GB, 8GB}`.
- For each `(method, budget)` pair compute all scores.
- Produce frontier plots per split: `error vs walltime` (all methods overlaid), `error vs expression_size` (all methods), `win-rate matrix` (method × method at each budget).

### Phase 4 — Remove q_height cap + saturation analysis (3–5 days)

- Parametrize `q_height` via config flag (currently hard-coded 14).
- Run depth-scaling experiments at `q_height ∈ {14, 20, 32, 64, 128}` on CANB-Poly.
- Show which "saturation" was implementation cap vs structural.

### Phase 5 — Theorem (1–3 weeks, parallel with Phase 3)

Minimum viable theorem:

> **Theorem 1 (Depth-1 completeness).** For target `α ∈ [-1, 1]`, max height `H`, max radicand `M`, the AEAS depth-1 float-prefilter + heap pipeline with heap size `≥ K_crit(H, M)` returns, up to canonicalization, every expression of form `A + B·sqrt(m)` with `A, B ∈ Q_H`, `m ∈ SqFree(M)`, that achieves absolute error below a threshold `τ_materialize`.

Plus a complexity lemma per stage.

Stronger (if time): connect observed slope `log error ~ α · log H` at depth 1 to a known Roth/Liouville-type exponent for `cos(2π/n)` — this is publishable on its own at JSC.

### Phase 6 — Paper writing (2 weeks)

Fill skeleton in `aeas_paper.tex`. Target 12–15 pages + appendix.

### Phase 7 — Release (3–5 days)

- Public GitHub repo with tagged release.
- Zenodo DOI for benchmark data.
- Leaderboard page (static HTML) reading from `benchmark/scores/`.
- Submission template + example.

---

## 5. Venue strategy

Primary submission (pick one; write for that venue first):

| Venue | CFP window | Pros | Cons |
|---|---|---|---|
| **NeurIPS 2026 D&B** | May abstract / May paper | Benchmark framing perfect fit; high visibility | ML reviewer pool may find math flavor odd |
| **AAAI 2027 Datasets** | Aug 2026 submission | Good fit, ML+AI reviewers | Later deadline |
| **ISSAC 2026** | Feb 2026 — **MISSED** | Symbolic-computation native audience | Timing |
| **Journal of Symbolic Computation** | rolling | Perfect community; JSC = Q1 math-CS | Slow, needs theorem strong |
| **Math. Comp.** | rolling | Prestigious | Demands heavier theorem |
| **Experimental Mathematics** | rolling | Lower bar on theorem, benchmark-friendly | Lower impact |
| **ACM TOMS** | rolling | Software quality recognized | Needs polished codebase + benchmark |

Recommended path: **NeurIPS D&B 2026 → JSC extended version** if accepted, or **ISSAC 2027** if not. Start writing for D&B deadline to force benchmark-centric framing.

---

## 6. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Benchmark "too niche" for ML D&B reviewers | High | Frame as instance of program synthesis for algebraic constants. Cite SRBench++, MATH dataset, MiniF2F. Emphasize reproducibility. |
| PSLQ or LLL outperforms AEAS on most tasks | Medium | Good result, not bad. Paper becomes "when is each method better" — still publishable. Adjust framing to complementary-baselines rather than Pareto-dominance. |
| Tree-GP wins on CANB-Rand | Low-Medium | Expected; CANB-Rand is a control. Highlight CANB-Poly and CANB-NestedRef as AEAS strongholds. |
| Theorem is wrong / trivial | Medium | Start with depth-1 completeness — mechanical to prove. |
| Effort overrun | High | Phase gates: if Phase 1 slips past 3 weeks, downgrade CANB size to ~100 tasks and PySR-only baseline. |
| Compute budget overrun | Medium | 600s/task cap keeps total bench ≤ 1 core-week per method. Run in parallel on 16-core box overnight. |
| LLM-baseline result awkward (LLM wins or loses dramatically) | Medium | Position as orthogonal capability probe; keep optional. |

---

## 7. Scoring formalism (spec)

Given method `M`, task `t`, submission `s = (expr, walltime, memory)`:

- `e(s) = |eval_1000dps(expr) − target|` (clamped to `1e-100` for log).
- `k(s) = node_count(expr)` (after canonicalization).
- `w(s) = walltime_sec(s)`.

Normalized point per task: `p_t(s) = (log10 e(s), log10 k(s), log10 w(s))` mapped to `[0,1]^3` against a fixed reference box `(log10 e ∈ [−30, 0], log10 k ∈ [0, 3], log10 w ∈ [−3, 3])`.

Per-task Pareto hypervolume `HV_t(M)` = hypervolume of points dominated by `p_t(s)` in `[0,1]^3`.

Per-split score: `Score(M, split) = mean_t HV_t(M)`.

Report tuple: `(Score, win-rate-at-60s-vs-best, median error at best budget, exact-solution rate)`.

---

## 8. Concrete immediate next steps

In order, with estimated effort:

1. **[0.5 day]** Review + confirm `report/aeas_paper.tex` skeleton, `report/benchmark_spec.md`, this plan.
2. **[0.5 day]** Define target task JSON schema finally. Freeze `benchmark/schema.json`.
3. **[1 day]** Write `scripts/generate_benchmark.py` — emit CANB-Poly + CANB-Trig first (smallest, fastest).
4. **[2 days]** Write AEAS submission adapter + harness runner for one split end-to-end.
5. **[3 days]** Continued fractions + PSLQ baselines (fastest to implement).
6. **[4 days]** PySR baseline integration.
7. **[1 day]** First full-split frontier plot.
8. **[Ongoing from week 2]** Theorem draft in parallel.

Stop-the-world checkpoint at step 7: produce the first real frontier plot. If it shows no coherent story (e.g. PSLQ dominates everywhere), regroup before investing in the remaining baselines.

---

## 9. File map

```
report/
  PLAN.md                     # this doc
  aeas_paper.tex              # new skeleton (Track A)
  benchmark_spec.md           # full CANB spec
  archive/
    PLAN_v1.md                # old plan (n=7,11,13 cos approximation)
    aeas_paper_v1.tex         # old paper draft
  research_pack/              # unchanged
benchmark/
  schema.json                 # task JSON schema (to be created)
  tasks/                      # generated task files
  submissions/<method>/       # per-method outputs
  scores/                     # scored results
scripts/
  generate_benchmark.py       # to be written
  run_benchmark.py            # to be written
  score_benchmark.py          # to be written
  baselines/
    cf.py, pslq.py, lll.py, pysr.py, mcts.py, bruteforce.py
src/aeas/baselines/           # harness-callable interfaces
```

---

## 10. Paper skeleton (summary; full text in `aeas_paper.tex`)

Section order:

1. **Introduction.** Problem = algebraic-number approximation via bounded-height constructible expressions. Gap = no benchmark. Contributions.
2. **Related work.** Denesting (Landau/Zippel/Blömer). Symbolic regression + deterministic enumeration (Kammerer 2021, Kahlmeyer 2024, França 2018). Diophantine approximation theory (Roth, Schmidt, Bugeaud). Integer-relation detection (PSLQ, LLL). Why none of these is a benchmark.
3. **CANB benchmark.** Task families, schema, scoring, splits, submission protocol.
4. **Reference method — AEAS.** Field-first architecture (reused from v1 paper), shrunk to 3–4 pages.
5. **Baselines.** Six baselines; how each adapts to the harness.
6. **Experiments.**
   - Frontier plots per split at matched compute.
   - Per-target-family wins.
   - Saturation analysis with exposed `q_height`.
   - Ablation: AEAS without field-first (= beam), without float prefilter, without diversity pruning.
7. **Theorem: depth-1 completeness.**
8. **Discussion & limitations.** When each method wins. Honest about degree-2-only tower.
9. **Conclusion.** Benchmark release. Leaderboard live at `<url>`.

---

## 11. Locked decisions (v0.1)

- **Benchmark size v0.1:** ~125 tasks. Families: `canb-poly` (~60), `canb-trig` (~50), `canb-transcend` (~10). `canb-nestedref`, `canb-algdeg`, `canb-rand` deferred to v0.2. All self-generating from `mpmath` + seed; no external dataset required. LMFDB considered for v0.2 `canb-algdeg`.
- **LLM baseline:** included, via **local LLMs** (Ollama / llama.cpp / vLLM). No proprietary API. Candidate models: `qwen2.5-coder:32b`, `deepseek-coder-v2`, `llama-3.1-70b-instruct`, `gemma-2-27b`. Interface: local HTTP server with OpenAI-compatible endpoint; structured-output via JSON-schema constrained decoding (grammar-guided or `response_format`). Method ids: `llm-local-<model>-<config>`. Walltime + VRAM + parameter count reported as budget; no dollar cost. Matched-compute framed against AEAS CPU walltime with honest disclaimer.
- **Primary venue:** **Journal of Symbolic Computation (JSC)** first. **ISSAC 2027** short / software track as parallel six months later. NeurIPS D&B skipped for v0.1; reconsider for v1.0.
- **Authorship:** solo draft to submission-ready → brief advisor at Bahçeşehir CENG with 1-page summary + `audit.md` → add advisor as co-author. arXiv preprint day 1 of submission. External collaborators (Turkish algebra groups, ISSAC PC, França, Kammerer) cold-contacted only post-preprint.
