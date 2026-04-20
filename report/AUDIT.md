# Q1 Research-Direction Audit — CANB Reframing

**Last updated:** 2026-04-20 (initial draft by Claude Opus 4.7)
**Owner:** Bato (noutry@gmail.com)
**Goal:** ship AEAS → CANB paper to a Q1 computational-math / CS venue.
**Why this file:** self-contained, resumable progress tracker. Any future agent (Claude or Codex) picks up from §8 "Resume Protocol" + §9 "Codex Directives".

---

## 0. TL;DR

Old paper (approximate tridecagon by ruler/compass) was rejected repeatedly — "too
specific, too art-oriented." Reframing pivots the contribution from *three
polygons* to a general benchmark (**CANB**) + reference method (**AEAS**) +
baseline suite. Infrastructure D1–D9 plus Week-2 W1/W2/W3 are done.
Remaining blockers for Q1 are: weak external-baseline coverage, unreleased
`q_height` cap, missing matched-compute frontier, missing theorem, missing
ablations, paper skeleton still full of TODOs, positioning vs 2024–2026
symbolic-regression / integer-relation literature not independently verified.

**Primary venue:** Journal of Symbolic Computation (JSC).
**Parallel:** ISSAC 2027 software track.
**Fallback:** NeurIPS D&B 2026 (benchmark framing) / *Experimental Mathematics*.

---

## 1. Audit Verdict (as of 2026-04-20)

The reframing is plausible and the infrastructure is real. The paper is *not*
Q1-ready yet. Gap list mirrors `audit.md` §5 but is now operationalized against
current repo state:

| Blocker | Status | Effort | Ref |
|---|---|---|---|
| Benchmark breadth (canb-poly ✓, canb-trig generated but unrun, canb-algdeg/nestedref/rand missing) | partial | 3–5 d | §2.A |
| Matched-compute Pareto frontier (error × nodes × walltime sweep) | not started | 2–4 d | §2.B |
| External baselines: PSLQ weak, LLL/PySR/MCTS/LLM absent | 1 of 5 real | 1–2 wk | §2.C |
| `q_height ≤ 14` core cap still protected; adapter knob only lowers it | partial | 2–5 d core change | §2.D |
| Theorem (depth-1 completeness + per-stage complexity) | not drafted | 1–3 wk | §2.E |
| Uncertainty / multi-seed / multi-hardware runtime | not started | 1–3 d | §2.F |
| Paper body filled (currently mostly TODOs past §4) | skeleton only | 2 wk | §2.G |
| Independent literature check vs 2025–2026 work (scoop risk) | not run | 1 d codex+consensus | §2.H |
| PSLQ genuine-relation rate 0/172 → effectively not a comparator | weak | 2–3 d | §2.C.ii |

Acceptance estimate without further work: <10% JSC, <5% TOMS. With §2.A–E done:
~25–40% JSC, ~30–45% NeurIPS D&B.

---

## 2. Open Work — Priority Ordered

Each block is intentionally small enough to be a single Codex task. Prompts are
in §9.

### A. Benchmark breadth
- Run matched AEAS+CF+PSLQ on `canb-trig` (50 tasks, already generated).
- Decide: ship v0.1 with 3 families (`canb-poly`, `canb-trig`, `canb-transcend`)
  OR add `canb-nestedref` (smaller, high-signal). Recommendation: add nestedref
  — Ramanujan-style radicals are where AEAS "should win" and the story needs a
  family where it wins by construction.
- Defer `canb-algdeg` and `canb-rand` to v0.2 (PLAN §11 already locks this).

### B. Matched-compute frontier
- Sweep `budget.walltime_sec ∈ {1, 10, 60, 600}` per (method, task) on canb-poly
  + canb-trig.
- `scripts/plot_frontier.py` does not exist yet. Spec: input is score CSVs,
  output is PNG per split with (error, walltime) scatter + Pareto front overlay
  per method.
- Replaces ad-hoc win/loss tables with one figure the reviewer pool respects.

### C. External baselines
  i. **Strengthen PSLQ.** Current `baselines/pslq.py` returns rational fallback
     for every task. Needs: basis `{1, √m_1, √m_2, √(m_1·m_2), …}` up to
     radicand 30, depth 2, with reporting of `relation_found=true|false` — and
     when true, emit the canonical AST. Use `mpmath.pslq` with a coefficient-
     bound and a digits-of-precision sweep.
  ii. **Add LLL.** `fpylll` over tower basis coefficients. One new file
      `src/aeas/baselines/lll.py` + tests. Matches PSLQ interface.
  iii. **Add PySR / tree-GP.** Operators `{+,−,×,÷,√}`, target = constant
       function. Cache model per task family; PySR start-up dominates.
  iv. **Optional: local LLM.** Ollama endpoint, JSON-schema constrained decoding
      to force AST output. Qwen2.5-Coder-32B / DeepSeek-Coder-V2 as initial
      candidates. Budget reported in (walltime, VRAM, param count).
  v. **Brute-force enum** at depth≤2, H≤8 as ground-truth reference on small
     tasks. ~100 lines.

### D. Expose `q_height`
- File: `src/aeas/field_search.py` (PROTECTED legacy; §11 lock).
- Current blocker: line hard-codes `q_height = min(max_height, 14)`. Adapter
  knob `--aeas-q-height-cap N` can only *lower* it. Raising it requires a core
  change. Decide: (a) break the lock for this one function parameter, or (b)
  ship v0.1 with the cap documented as an architectural choice and sweep only
  downward values. Recommendation (a): convert `14` to a parameter with default
  14, preserving bit-identical behavior unless explicitly raised.
- Re-run AEAS with `q_height ∈ {14, 20, 32, 64}` on canb-poly. Plot: saturation
  at each cap level to separate algorithmic from cap-induced saturation.

### E. Theorem
- **Minimum viable:** Theorem 1 (depth-1 completeness) as drafted in `aeas_paper.tex`
  §7 + per-stage complexity lemma. Proof sketch already implicit in the heap-
  size bound `K_crit`. Formalize bounds; cite Landau 1989 for canonicalization.
- **Stronger (optional):** connect observed `log(error) ~ α·log(H)` slope to a
  Roth/Liouville-type exponent for `cos(2π/n)`. Cite Bugeaud 2004.
- Prose target: 1–1.5 pages in paper body + 2–3 pages proof appendix.

### F. Robustness
- 5 hardware/seed repeats of canb-poly AEAS run, report median + IQR on
  walltime. Stochastic baselines (PySR, MCTS, LLM) get multi-seed CIs.

### G. Paper body
- Fill `aeas_paper.tex` sections 4 (AEAS — has pseudocode TODO), 5 (baselines —
  needs code refs after §2.C lands), 6 (results — needs frontier figures from
  §2.B), 7 (theorem from §2.E), 8 (discussion). Target 12–15 pages.
- Add author block + affiliation.

### H. Independent positioning check
- Codex + Consensus literature sweep (see §9.A). Specifically look for 2025–2026
  work that might scoop CANB: algebraic-constant benchmarks, constructible-
  number search, denesting-benchmark datasets, Poëls 2025 (*Annals of Math.*
  approximation bounds), recent integer-relation / PSLQ extensions.
- Expected outcome: either confirm the gap is still open, or surface a paper
  that forces a repositioning.

---

## 3. Current Repo State (snapshot 2026-04-20)

From `report/STATUS.md` and `report/EXPERIMENTS.md`:

- Tests: **150 passed, 14 warnings** (`/Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/ -q`).
- v0.1 tasks generated: 222 total. Splits under `benchmark/tasks/`:
  - `canb-poly` — 167 tasks (non-GW `n ∈ [7, 200]`)
  - `canb-trig` — 50 tasks (generated, not yet run)
  - `canb-transcend` — 5 tasks
- Scored runs:
  - AEAS × canb-poly, canb-transcend
  - CF × canb-poly, canb-transcend
  - PSLQ × canb-poly, canb-transcend (all `relation_found=false`)
- Canonical primary-metric table (canb-poly, 167 tasks):

  | method | median error | median nodes | median walltime | exact rate |
  |---|---:|---:|---:|---:|
  | aeas | 1.59e-8 | 11 | 1.29 s | 0 |
  | cf | 7.81e-4 | 1 | 3.3e-4 s | 0 |
  | pslq | 7.81e-4 | 1 | 0.33 s | 0 |

- Frontier: 167/167 non-dominated across (error, nodes, walltime). AEAS is sole
  occupant of the low-error region; CF/PSLQ occupy the low-size/low-time region.
  Story: "complementary regimes," not "AEAS dominates."

**Protected-core policy:** `src/aeas/{expr, canonicalize, evaluate, field_search,
search, chebyshev}.py` untouched. Lifting `q_height` cap requires breaking this.

---

## 4. Venue Decision Tree

```
Theorem drafted AND frontier plots clean?
├── YES → JSC primary (best fit; slow but Q1 math-CS).
│         Parallel arXiv preprint day-1. ISSAC 2027 short paper 6 mo later.
└── NO  → NeurIPS D&B 2026 (benchmark framing; deadline May paper).
          Weaker theorem acceptable; stronger code artifact required.
          Experimental Mathematics (theorem-optional) as fallback.
```

Kill-switch triggers (from ROADMAP §"Hard stops"):
- PSLQ Pareto-dominates AEAS everywhere → reframe as "when is PSLQ not enough."
- Theorem blocks >5 days → drop to NeurIPS D&B / Experimental Mathematics.
- Compute > 2 core-weeks per method → shrink benchmark or drop slowest baseline.

---

## 5. Scoop Risk (high-level, to be verified by §2.H codex run)

Known adjacent 2021–2026 work from `audit.md`:
- Kammerer 2021, Kahlmeyer 2024 — deterministic SR with semantic dedup. Closest
  prior art for the "field-first beats syntax-first" claim. AEAS differentiator
  = explicit quadratic tower + delayed materialization + constructible target.
- Osipov 2021 — nested-radical denesting (inverse problem, not forward search).
- Poëls 2025 *Annals of Math.* — approximation by bounded-degree algebraic
  numbers. Theory-side only; no algorithm. Good citation, not a scoop.
- No public benchmark currently exists for the forward search problem. This is
  the load-bearing claim CANB rests on. Needs §2.H confirmation before
  submission.

### 5.1 Positioning sweep 2026-04-20

**Final verdict:** scope still open. Consensus searches over the required eight
queries, plus exact arXiv/web searches for `"constructible number approximation
benchmark"`, `"quadratic tower normal form search"`, and related phrases found
no 2024--2026 paper that benchmarks forward search for bounded-height
constructible/nested-square-root approximations, and no paper using AEAS's
specific field-first quadratic-tower normal-form enumeration with delayed tree
materialization. The risk is not a direct scoop; it is reviewer pushback that
CANB is "just another symbolic-regression benchmark" unless the paper sharply
separates constant approximation in a constructible grammar from data-fitting SR.

**Relevant hits and overlap verdicts**

- **Paul Kahlmeyer, Joachim Giesen, Michael Habeck, Henrik Voigt, "Scaling Up
  Unbiased Search-based Symbolic Regression," IJCAI 2024.** Systematic search
  over small expressions outperforms stochastic SR methods on established
  function-regression benchmarks. **Verdict: adjacent-cite-required.** Closest
  algorithmic positioning threat for "syntax-first systematic search"; not a
  benchmark for algebraic constants or constructible towers.
- **Gabriel Kronberger, Fabricio Olivetti de Franca, Harry Desmond, Deaglan J.
  Bartlett, Lukas Kammerer, "The Inefficiency of Genetic Programming for
  Symbolic Regression," PPSN 2024.** Uses exhaustive enumeration/equality
  saturation to compare GP against search over semantically unique expressions.
  **Verdict: adjacent-cite-required.** Strong support for AEAS's anti-redundancy
  motivation; not a CANB scoop because tasks are regression datasets, not
  numeric constants in quadratic fields.
- **Marcel Anselment, Moritz Neumaier, Stephan Rudolph, "Systematic tree search
  for symbolic regression: deterministically searching the space of
  dimensionally homogeneous models," CEAS Aeronautical Journal, online 2025 /
  vol. 17, 2026.** Deterministic tree search for dimensionally homogeneous SR,
  with Pareto analysis over accuracy and complexity. **Verdict:
  adjacent-cite-required.** Reinforces need to frame AEAS as field-indexed
  algebraic search, not generic deterministic tree search.
- **F. O. de Franca et al., "SRBench++: Principled Benchmarking of Symbolic
  Regression With Domain-Expert Interpretation," IEEE TEVC 2025
  (DOI assigned 2024).** Expands SRBench with interpretability and
  domain-expert evaluation. **Verdict: adjacent-cite-required.** It is the
  benchmark paper reviewers will compare against; CANB must say SRBench++ fits
  functions from data, while CANB scores AST-valued approximations to fixed
  high-precision constants.
- **Guilherme S. Imai Aldeia et al., "Call for Action: Towards the Next
  Generation of Symbolic Regression Benchmark," GECCO Companion 2025.** Calls
  for living SRBench governance, standardized compute, energy, complexity, and
  method maintenance. **Verdict: adjacent-cite-required.** Useful for benchmark
  protocol language; not a constructible-number benchmark.
- **Viktor Martinek, "Fast Symbolic Regression Benchmarking," arXiv 2025 /
  LNCS 2026.** Improves SR benchmark mechanics via acceptable-expression sets
  and early-termination callbacks. **Verdict: adjacent-cite-required.** CANB can
  borrow the "multiple acceptable forms" argument for equivalent ASTs, but the
  target problem remains regression rediscovery.
- **L. G. A. dos Reis, V. L. P. S. Caminha, T. J. P. Penna, "Benchmarking
  symbolic regression constant optimization schemes," arXiv 2024.** Compares
  numerical optimization methods for constants inside GP/SR expressions and
  proposes tree-edit distance for symbolic accuracy. **Verdict: tangential.**
  "Constant optimization" here means fitting parameters inside SR models, not
  approximating mathematical constants by algebraic expressions.
- **Junlan Dong, Jinghui Zhong, "Recent Advances in Symbolic Regression," ACM
  Computing Surveys 2025.** Survey covering SR definitions, benchmarks,
  deterministic methods, GP, and neural methods. **Verdict:
  adjacent-cite-required.** Good survey citation for related work; no CANB-like
  constant-approximation benchmark surfaced.
- **Anthony Poëls, "On approximation to a real number by algebraic numbers of
  bounded degree," Annals of Mathematics 2025.** Improves Wirsing-type lower
  bounds for approximation by algebraic numbers of bounded degree. **Verdict:
  tangential but important theory citation.** It studies asymptotic existence
  bounds, not algorithms, expression-size scoring, or constructible-depth
  benchmarks.
- **Yingfan Hua et al., "Finetuning Large Language Model as an Effective
  Symbolic Regressor," arXiv 2025 / withdrawn ICLR 2026 submission.** Introduces
  SymbArena, a large equation corpus for LLM symbolic regression. **Verdict:
  tangential.** Relevant only to optional local-LLM baselines; not constructible
  approximation or algebraic-number search.

**Citations to add/update in `aeas_paper.tex` bibliography**

```bibtex
@inproceedings{kahlmeyer2024scaling, author={Paul Kahlmeyer and Joachim Giesen and Michael Habeck and Henrik Voigt}, title={Scaling Up Unbiased Search-based Symbolic Regression}, booktitle={Proceedings of IJCAI 2024}, pages={4264--4272}, year={2024}, doi={10.24963/ijcai.2024/471}}
@inproceedings{kronberger2024inefficiency, author={Gabriel Kronberger and Fabricio Olivetti de Franca and Harry Desmond and Deaglan J. Bartlett and Lukas Kammerer}, title={The Inefficiency of Genetic Programming for Symbolic Regression}, booktitle={PPSN XVIII}, series={LNCS}, volume={15148}, pages={273--289}, year={2024}}
@article{anselment2026systematic, author={Marcel Anselment and Moritz Neumaier and Stephan Rudolph}, title={Systematic tree search for symbolic regression: deterministically searching the space of dimensionally homogeneous models}, journal={CEAS Aeronautical Journal}, volume={17}, pages={793--808}, year={2026}, doi={10.1007/s13272-025-00886-3}}
@article{dong2025recent, author={Junlan Dong and Jinghui Zhong}, title={Recent Advances in Symbolic Regression}, journal={ACM Computing Surveys}, volume={57}, number={11}, pages={1--37}, year={2025}, doi={10.1145/3735634}}
@inproceedings{aldeia2025call, author={Guilherme S. Imai Aldeia and Hengzhe Zhang and Geoffrey Bomarito and Miles Cranmer and Alcides Fonseca and Bogdan Burlacu and William G. La Cava and Fabricio Olivetti de Franca}, title={Call for Action: Towards the Next Generation of Symbolic Regression Benchmark}, booktitle={GECCO 2025 Companion}, pages={2529--2538}, year={2025}, doi={10.1145/3712255.3734309}}
@misc{dosreis2024constantopt, author={L. G. A. dos Reis and V. L. P. S. Caminha and T. J. P. Penna}, title={Benchmarking symbolic regression constant optimization schemes}, year={2024}, eprint={2412.02126}, archivePrefix={arXiv}, primaryClass={cs.LG}}
@misc{martinek2025fastsrbench, author={Viktor Martinek}, title={Fast Symbolic Regression Benchmarking}, year={2025}, eprint={2508.14481}, archivePrefix={arXiv}, primaryClass={cs.LG}}
```

**Highest-priority follow-ups**

1. Add one paragraph in Related Work explicitly distinguishing CANB from
   SRBench/SRBench++/SymbArena: fixed high-precision constants, constructible
   AST grammar, and error-size-walltime scoring.
2. Strengthen baselines with a serious deterministic SR comparator
   (Kahlmeyer-style or PySR with constant-target setup) and a tree-dedup
   ablation, because the closest overlap is algorithmic, not benchmark-level.
3. Keep the "first benchmark" claim narrow: "first benchmark for bounded-height
   constructible approximation of real numbers," not "first algebraic symbolic
   search benchmark" or "first constant discovery benchmark."

**Audit of §5.1 (by Claude Opus 4.7, 2026-04-20):**

- Verdict accepted: no 2024–2026 scoop. Dominant risk is framing, not priority.
- Citation hygiene: three entries codex proposed duplicate existing paper bib:
  `kahlmeyer24` ↔ `kahlmeyer2024scaling`, `franca24srbenchpp` ↔ SRBench++
  (paper currently dates it 2024; codex says 2025 — online-first 2024, issue
  2025, resolve to 2025 at update), `poels25` ↔ already present. When merging,
  edit the existing bibkeys, do not add parallel entries.
- New, non-duplicate citations to add: `kronberger2024inefficiency`,
  `anselment2026systematic`, `dong2025recent`, `aldeia2025call`,
  `martinek2025fastsrbench`. `dosreis2024constantopt` can be skipped (codex
  flagged tangential).
- Follow-up #2 (deterministic-SR comparator) coincides with §2.C.iii PySR
  baseline. Prefer Kahlmeyer 2024 as the named comparator in prose even if
  the implementation is PySR, because Kahlmeyer is the algorithmic sibling
  reviewers will expect to see contrasted.
- Follow-up #3 framing: already implicit in `OVERVIEW.md` elevator pitch;
  propagate the exact phrase "first benchmark for bounded-height
  constructible approximation of real numbers" into the paper abstract +
  introduction first sentence.

---

## 6. Dependencies / Environment

- Python interpreter: `/Users/bato/micromamba/envs/aeas/bin/python` (plain
  `python` is NOT on PATH).
- Tests: `/Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/ -q`.
- Current deps (pyproject): `mpmath`, `sympy`, `numpy`, `pytest`, `jsonschema`.
  Future baselines need: `fpylll` (LLL), `pysr` (tree-GP — heavy Julia dep),
  optional `ollama` / OpenAI-compatible HTTP client (local LLM).
- No network access in the Python env during test runs.

---

## 7. Progress Log

- **2026-04-20** — Initial audit doc created by Claude. Infrastructure D1–D9 +
  Week-2 W1/W2/W3 already complete per `STATUS.md`. 150 tests green.
  Next scheduled action: §9.A codex Consensus positioning sweep.
- **2026-04-20** — §9.A executed via `codex exec` (model gpt-5.4, reasoning
  high, sandbox danger-full-access, Consensus MCP). Result appended as §5.1.
  Verdict: scope still open; no direct scoop. 5 new citations to merge into
  `aeas_paper.tex` bib (see audit under §5.1). §2.H marked addressed once bib
  merge lands. Next scheduled action: pick one of §9.B (PSLQ strengthen) or
  §9.C (matched-compute frontier). Recommendation: §9.C first — unblocks
  §2.B, §2.G results section, and produces the figure reviewers expect; PSLQ
  strengthening is smaller-scope and can run in parallel later.

Append new entries dated (ISO 8601). Each entry: what was done, test count
delta, blocker notes, next action.

---

## 8. Resume Protocol (for the next agent)

If you are picking this up cold, do this in order:

1. `cd /Users/bato/MyProjects/automated-euclidean-approximation-system`
2. Read in order: `report/OVERVIEW.md`, `report/PLAN.md` §11, this file,
   `report/EXPERIMENTS.md`, `report/STATUS.md` (tail of file), `audit.md` §5.
3. Run `/Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/ -q` to
   confirm baseline state. Expected: 150 passed (or higher).
4. Look at §2 for the next highest-priority unchecked block. Pick the codex
   directive from §9 that matches.
5. Append to §7 Progress Log when done.

**Hard rules to preserve:**
- Do NOT delete `results/` or `report/archive/` — historical record.
- Do NOT modify `src/aeas/{expr, canonicalize, evaluate, field_search, search,
  chebyshev}.py` beyond adding (not changing) public helpers, UNLESS the task
  explicitly is the §2.D `q_height` lift — in which case the commit message
  must flag the lock break.
- Do NOT auto-commit. User commits manually.
- Do NOT write emojis in files.
- Seed every new RNG path. No wall-clock randomness.

---

## 9. Codex Directives (ready to paste)

Codex is invoked via:

```bash
codex exec --sandbox <mode> --full-auto --skip-git-repo-check \
  -C /Users/bato/MyProjects/automated-euclidean-approximation-system \
  -m gpt-5-codex \
  --config model_reasoning_effort="high" \
  "$(cat <<'PROMPT'
<prompt body here>
PROMPT
)" 2>/dev/null
```

Select `--sandbox read-only` for audits; `workspace-write` for code tasks.
For resume: `echo "<followup>" | codex exec --skip-git-repo-check resume --last 2>/dev/null`.

Each of the prompts below is self-contained. Paste the body into the PROMPT
heredoc and run.

---

### 9.A — Literature positioning sweep (Consensus + codex)

**Purpose:** §2.H. Confirm CANB is not scooped. Sandbox: read-only + network
(needs Consensus MCP or web).

```
You are auditing the research positioning of a paper in progress at the repo
/Users/bato/MyProjects/automated-euclidean-approximation-system.

READ FIRST (in order):
  report/OVERVIEW.md
  report/PLAN.md §1, §2, §3, §11
  report/AUDIT.md (this tracker)
  audit.md §2 (prior literature scan)
  report/aeas_paper.tex (intro + related work)

GOAL
Verify that no 2024–2026 paper scoops CANB or the field-first AEAS contribution.
Use Consensus (preferred) and/or arXiv full-text search. Report findings as an
appendix to report/AUDIT.md §5 "Scoop Risk". Do NOT modify source code.

QUERIES to run (minimum; add more if you spot adjacent terminology):
  1. "constructible number approximation benchmark"
  2. "nested radical search algorithm symbolic regression"
  3. "bounded height algebraic approximation enumeration"
  4. "quadratic tower search algorithm normal form"
  5. "symbolic regression benchmark constant approximation"
  6. "PSLQ LLL algebraic relation benchmark 2024 2025 2026"
  7. "denesting algorithm benchmark dataset"
  8. "algebraic constant discovery neural symbolic"

FOR EACH HIT published 2024–2026 report:
  - Title, authors, venue, year.
  - One-paragraph summary.
  - Overlap-with-CANB verdict ∈ {scoop, adjacent-cite-required, tangential}.
  - If "scoop": propose a repositioning sentence for the CANB abstract.

DELIVERABLE
Append to report/AUDIT.md a new section "§5.1 Positioning sweep <date>" with:
  - Final verdict: scope still open / partial overlap / scooped.
  - Citations to add to aeas_paper.tex bibliography (BibTeX-ready).
  - At most 3 highest-priority follow-ups for the author.

Do NOT modify aeas_paper.tex directly. Write-only to AUDIT.md.
Keep output under 1500 words.
```

---

### 9.B — PSLQ strengthening

**Purpose:** §2.C.i. Sandbox: workspace-write.

```
You are extending the PSLQ baseline at
/Users/bato/MyProjects/automated-euclidean-approximation-system.

READ FIRST:
  src/aeas/baselines/pslq.py
  src/aeas/methods.py
  src/aeas/ast_io.py
  report/benchmark_spec.md §4 (AST grammar)
  report/EXPERIMENTS.md (PSLQ weakness notes)

GOAL
Turn PSLQ from rational-fallback-only into a real symbolic competitor on
canb-poly and canb-transcend.

CHANGES
1. Expand PSLQ basis: {1, √m1, √m2, √(m1·m2)} for m_i in squarefree integers
   up to radicand 30. Include depth-2 products.
2. Sweep mpmath working precision {50, 100, 200} dps; accept first relation
   whose magnitude bound passes.
3. When a relation is found, emit the canonical AST via src/aeas/ast_io.py
   (ADD/MUL/SQRT/CONST). Else fall back to best rational convergent.
4. Set submission.notes to begin with "relation_found=true|false;"
   followed by basis digest and precision used.
5. Add tests/test_pslq_baseline.py cases:
   - A handcrafted target that IS √2 + √3 — must recover as relation.
   - cos(2π/7) — PSLQ cannot find exact relation; must fall back.
   - Determinism: same task + seed → byte-identical submission.

RUN AFTER
  /Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/ -q
  /Users/bato/micromamba/envs/aeas/bin/python scripts/run_benchmark.py \
    --method pslq --split canb-poly --out benchmark/runs/pslq-v2-canb-poly/submissions
  /Users/bato/micromamba/envs/aeas/bin/python scripts/score_benchmark.py \
    --method pslq --split canb-poly \
    --submissions-dir benchmark/runs/pslq-v2-canb-poly/submissions \
    --out benchmark/runs/pslq-v2-canb-poly/score.csv

STOP when `relation_found=true` rate on canb-poly > 0 (even a single hit
confirms the basis is reaching algebraic structure). Record in
report/STATUS.md. Do NOT modify protected core files.
```

---

### 9.C — Matched-compute frontier + plot

**Purpose:** §2.B. Sandbox: workspace-write.

```
GOAL: implement `scripts/plot_frontier.py` and run a matched-budget sweep.

STEP 1. Sweep runner.
Extend scripts/run_benchmark.py OR wrap it in a new scripts/sweep_benchmark.py
that iterates budget.walltime_sec ∈ {1, 10, 60, 600} for --method in
{aeas, cf, pslq} across --split in {canb-poly, canb-trig, canb-transcend}.
Output: benchmark/runs/sweep-<method>-<split>-<budget>s/.

STEP 2. Scoring.
For each (method, split, budget), run scripts/score_benchmark.py. Aggregate
into benchmark/runs/sweep_summary.csv with columns
(method, split, budget_sec, median_error, median_nodes, median_walltime,
exact_rate, Cpath).

STEP 3. Plotting.
Write scripts/plot_frontier.py using matplotlib only. Inputs: sweep_summary.csv
and per-task score CSVs. Outputs per split, one PNG:
  - Scatter of (log10 walltime, log10 error), points colored by method.
  - Pareto front polyline per method.
  - Save to benchmark/figures/frontier_<split>.png.

STEP 4. Tests.
tests/test_plot_frontier.py: feed a synthetic 3-method × 4-budget CSV, assert
PNG is written + Pareto point count matches expectation.

STOP when all three splits have frontier PNGs under benchmark/figures/ and
the sweep CSV is committed-ready. Append STATUS.md entry with file paths.
Do NOT modify protected core. Budget-aware: if canb-poly × 600s × 3 methods
exceeds 4 hours wall, reduce to {1, 10, 60} for canb-poly and note in STATUS.
```

---

### 9.D — `q_height` cap lift (protected-core break)

**Purpose:** §2.D. Sandbox: workspace-write. **REQUIRES USER APPROVAL** before
running — this deliberately breaks the §11 lock.

```
TASK: parametrize the hard-coded q_height cap in src/aeas/field_search.py.

BACKGROUND
Line currently reads: q_height = min(max_height, 14).
Adapter knob --aeas-q-height-cap can only lower this. Scaling experiments in
the paper (saturation at H=32 vs H=64) require raising it.

CONSTRAINT: default behavior MUST remain bit-identical to pre-change runs.

CHANGES
1. Edit src/aeas/field_search.py: replace `14` with a module-level constant
   DEFAULT_Q_HEIGHT_CAP = 14, and add a parameter q_height_cap=None to the
   public search entry. Use DEFAULT_Q_HEIGHT_CAP if None.
2. Edit src/aeas/canb_adapter.py to forward budget["aeas_q_height_cap"] to
   the new parameter, preserving lowering behavior and enabling raising.
3. Add test: tests/test_q_height_lift.py verifying default run bit-matches a
   frozen golden submission for canb-transcend-pi, AND that q_height_cap=32
   produces a strictly different submission set on n=13.
4. Re-run: python scripts/run_benchmark.py --method aeas --split canb-poly \
     --aeas-q-height-cap 32 --out benchmark/runs/aeas-qh32-canb-poly/submissions
   Then score. Write summary to STATUS.md with delta vs default.
5. Update report/AUDIT.md §2.D: mark done, note commit needed to break lock.

RUN pytest tests/ -q to confirm 150+ still passing. If any pre-existing test
regresses, REVERT and report. Do not auto-commit.
```

---

### 9.E — LLL baseline

**Purpose:** §2.C.ii. Sandbox: workspace-write. Requires `fpylll` dep bump.

```
GOAL: add src/aeas/baselines/lll.py with solve(task, budget) -> submission.

INSTALL CHECK FIRST:
  /Users/bato/micromamba/envs/aeas/bin/python -c "import fpylll"
If missing, STOP and report — user must install it.

LOGIC
1. Build tower basis {1, √m1, …} same as PSLQ §9.B.
2. Construct integer lattice whose basis vectors are rounded multiples of the
   tower-basis evaluation at target precision.
3. LLL-reduce; first reduced vector gives candidate relation.
4. Emit AST same way as PSLQ; report basis digest + reduction parameters.
5. Tests analogous to test_pslq_baseline.py under tests/test_lll_baseline.py.
6. Register in src/aeas/methods.py as "lll".
7. Run lll on canb-transcend and canb-poly; score; log in STATUS.md.

Honour protected-core rule. No emojis. No auto-commit.
```

---

### 9.F — PySR / tree-GP baseline

**Purpose:** §2.C.iii. Sandbox: workspace-write + network (Julia bootstrap).

```
WARNING: PySR pulls Julia. Start-up is slow. Cache per task family.

GOAL: src/aeas/baselines/pysr_baseline.py with solve(task, budget).
Config: unary ops {sqrt}, binary ops {+,-,*,/}, niterations bounded by budget
walltime. Target is scalar constant — feed PySR a degenerate fitting problem
(X = random 10 rows, y = constant target).

Emit the smallest best-loss expression as AST via a dedicated
sympy → aeas-ast-v1 translator (new function in src/aeas/ast_io.py named
sympy_to_ast). Tests under tests/test_pysr_baseline.py.

If Julia bootstrap exceeds 10 minutes on first call, skip canb-poly in this
session and run only canb-transcend; flag in STATUS.md.
```

---

### 9.G — Theorem draft

**Purpose:** §2.E. Sandbox: read-only.

```
DRAFT: Theorem 1 (Depth-1 completeness) + per-stage complexity lemma.

READ FIRST
  report/aeas_paper.tex §7
  src/aeas/field_search.py (depth-1 path)
  src/aeas/canonicalize.py

DELIVERABLE
A markdown file report/theorem_draft.md containing:
  - Statement of Theorem 1 in clean notation.
  - Full proof (target 1.5–2.5 pages in paper).
  - Statement + proof of Lemma 1 (per-stage complexity).
  - At least one worked example showing K_crit computation for cos(2π/7),
    H=16, M=8.
  - Citation suggestions (Landau 1989 canonicalization bound; mpmath error
    bound literature).
  - Flag any implicit assumption in the current field_search pipeline that
    the theorem statement must surface (e.g., "canonical hash collision-
    freeness"). If collision-freeness is load-bearing, write it as a
    hypothesis rather than claiming it.

Do NOT modify aeas_paper.tex yet; this is a draft for Bato to review before
merging. No emojis.
```

---

### 9.H — canb-nestedref generation

**Purpose:** §2.A, optional inclusion in v0.1. Sandbox: workspace-write.

```
GOAL: extend scripts/generate_benchmark.py to emit canb-nestedref tasks.

SOURCES
  - Ramanujan's nested radical examples (6 classical from Ramanujan notebooks
    III, IV; reference values verified via sympy).
  - Textbook identities: √(5 + 2√6) = √2 + √3, √(3 + 2√2) = 1 + √2, etc.
  Aim for ~30 tasks total.

Each task: known_closed_form set (the exact AST), target_spec kind =
"ramanujan_radical". Reference value computed at 1100 dps.

Tests: tests/test_nestedref_generator.py determinism + byte-identity of
two consecutive generations. Update benchmark/MANIFEST.json.

Run AEAS + CF + PSLQ on the new split; expected outcome: AEAS recovers
the closed form or a low-error alternative in most tasks; PSLQ recovers it
exactly when radicand bases are inside the basis; CF degrades.

Log findings in STATUS.md + EXPERIMENTS.md.
```

---

## 10. Things NOT to do this round

- Do not generate `canb-algdeg` or `canb-rand` — deferred to v0.2.
- Do not integrate a commercial LLM API — local-only per PLAN §11.
- Do not refactor legacy AEAS internals for style.
- Do not write a "benchmark website / leaderboard HTML" yet; that is a Week-6
  deliverable, dependent on having scores for ≥4 methods.
- Do not commit on behalf of user.
