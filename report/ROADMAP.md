# AEAS → CANB Roadmap (Executable)

One-page action list. Use alongside `PLAN.md` and `benchmark_spec.md`.

## Week 1 — foundation

- [ ] Freeze task JSON schema → `benchmark/schema.json`. Reference: `benchmark_spec.md` §2, §4.
- [ ] Write `scripts/generate_benchmark.py`:
  - `--split {canb-poly, canb-trig, canb-transcend, canb-algdeg, canb-nestedref, canb-rand}`
  - `--version 0.1 --seed 20260420`
  - Emits `benchmark/tasks/<family>/<id>.json` + `benchmark/MANIFEST.json` with SHA256 per task.
- [ ] Generate `canb-poly` (non-GW `n ∈ [7, 200]`, ~60 tasks) + `canb-transcend` (5 tasks) first.
- [ ] Write AEAS submission adapter: `src/aeas/canb_adapter.py::solve(task, budget) -> submission_dict`.
- [ ] Write `scripts/run_benchmark.py --method aeas --split canb-poly --budget '{"walltime_sec":60}'`.
- [ ] Write `scripts/score_benchmark.py --submissions-dir ... --output benchmark/scores/aeas.csv`.
- [ ] End-to-end: one green run of `generate → aeas_submit → score` on `canb-poly`.

## Week 2 — cheap baselines

- [ ] `src/aeas/baselines/cf.py` (continued fractions). Use `fractions.Fraction`. ~50 lines.
- [ ] `src/aeas/baselines/pslq.py` — wrap `mpmath.pslq` against tower bases up to radicand 30 and depth 2. Emit canonical AST if relation found.
- [ ] Sanity: run CF + PSLQ on `canb-poly` + `canb-transcend`. Validate harness reports reasonable errors.

## Week 3 — heavy baselines

- [ ] `src/aeas/baselines/pysr_baseline.py`. Install PySR; operators `+ - * / sqrt`; target = constant function. Cache per-task — PySR start-up dominates.
- [ ] `src/aeas/baselines/lll_baseline.py` with `fpylll` over tower coefficients.
- [ ] `src/aeas/baselines/bruteforce.py` — exhaustive canonical enumeration up to `d=2, H=8`. Sanity reference for small tasks.
- [ ] (Optional) `src/aeas/baselines/mcts.py`.
- [ ] `src/aeas/baselines/llm_local.py` — local LLM via Ollama / llama.cpp / vLLM (OpenAI-compatible HTTP). JSON-schema constrained decoding for AST output. Retry on invalid AST up to 3×. Report walltime + VRAM + model parameter count as budget. Run multiple models as separate methods (e.g. `llm-local-qwen2.5-coder-32b`, `llm-local-deepseek-coder-v2`, `llm-local-llama-3.1-70b`).

## Week 4 — matched-compute runs + ablations

- [ ] Sweep `budget.walltime_sec ∈ {1, 10, 60, 600}` for every (method, task) pair on full benchmark. Parallelize across cores.
- [ ] Emit frontier plots: `scripts/plot_frontier.py --split canb-poly --axes error,walltime`.
- [ ] Remove `q_height <= 14` hard-code; re-run AEAS with sweep `q_height ∈ {14, 20, 32, 64, 128}`.
- [ ] AEAS ablation: disable field-first (= tree beam), disable diversity reservation, disable float prefilter. One frontier plot each.

## Week 5 — theorem + writing

- [ ] Draft proof of depth-1 completeness (PLAN.md §10; paper §7).
- [ ] Draft per-stage complexity lemma.
- [ ] Plot `log10 error vs log10 H` per family, fit slope. Compare against known Diophantine exponents (optional stronger claim).
- [ ] Paper full draft: fill TODOs in `aeas_paper.tex`. Target 12–15 pages.

## Week 6 — release + submission

- [ ] Public repo tagged `canb-v0.1`.
- [ ] Zenodo upload → DOI.
- [ ] Static leaderboard page rendered from `benchmark/scores/*.csv`.
- [ ] Submission template + reviewer reproduction guide.
- [ ] Submit to target venue. Recommended: NeurIPS D&B abstract by deadline; then paper.

---

## Hard stops / re-plan triggers

- If Phase 1 (week 1) overruns past 2 weeks → cut `canb-rand` and `canb-algdeg` from v0.1, ship with 4 families.
- If PSLQ Pareto-dominates AEAS on all families → reframe paper as "when is PSLQ not enough," AEAS becomes the method for when it isn't.
- If a theorem proof blocks for >5 days → ship without Theorem 1 and submit to *Experimental Mathematics* or NeurIPS D&B (theorem-optional venues) instead of JSC.
- If total compute cost exceeds 2 core-weeks per method → shrink benchmark or drop the slowest baseline.

---

## Repo layout target (end of Week 6)

```
.
├── AGENTS.md
├── README.md (rewrite for benchmark)
├── benchmark/
│   ├── MANIFEST.json
│   ├── schema.json
│   ├── tasks/
│   │   ├── canb-poly/*.json
│   │   ├── canb-trig/*.json
│   │   ├── canb-transcend/*.json
│   │   ├── canb-algdeg/*.json
│   │   ├── canb-nestedref/*.json
│   │   └── canb-rand/*.json
│   ├── submissions/
│   │   ├── aeas-v0.3/…
│   │   ├── cf/…
│   │   ├── pslq/…
│   │   ├── lll/…
│   │   ├── pysr/…
│   │   └── (optional) llm-claude-opus-4-7/…
│   └── scores/
│       ├── aeas.csv
│       ├── frontier_canb-poly.json
│       └── leaderboard.json
├── report/
│   ├── aeas_paper.tex
│   ├── PLAN.md
│   ├── ROADMAP.md
│   ├── benchmark_spec.md
│   ├── archive/
│   │   ├── PLAN_v1.md
│   │   └── aeas_paper_v1.tex
│   └── research_pack/
├── results/ (legacy; kept for reproducibility of v1)
├── scripts/
│   ├── generate_benchmark.py
│   ├── run_benchmark.py
│   ├── score_benchmark.py
│   ├── plot_frontier.py
│   ├── run_search.py (kept for AEAS direct invocation)
│   └── rerun_all.sh (kept, gated)
├── src/
│   └── aeas/
│       ├── (unchanged core files)
│       ├── canb_adapter.py
│       └── baselines/
│           ├── cf.py
│           ├── pslq.py
│           ├── lll_baseline.py
│           ├── pysr_baseline.py
│           ├── bruteforce.py
│           └── mcts.py (optional)
├── tests/ (+ tests for harness, schema, scorers)
└── audit.md (preserved as historical context)
```
