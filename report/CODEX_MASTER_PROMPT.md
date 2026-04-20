# Master Prompt — Convert AEAS Codebase into CANB Benchmark Framework

Use this as the single prompt for `codex exec` (or interactive codex). Copy the block below verbatim. It is self-contained: codex has no memory of the prior chat.

---

## THE PROMPT

```
You are operating on the repository at /Users/bato/MyProjects/automated-euclidean-approximation-system.
Treat this as a long-running engineering task. Run commands, read files, edit files, and write tests.

BACKGROUND (read in this order before doing anything else):
  1. report/OVERVIEW.md       — plain-language project summary
  2. report/PLAN.md            — strategy and locked decisions (esp. §11)
  3. report/ROADMAP.md         — week-by-week checklist (you will execute Week 1 + part of Week 2)
  4. report/benchmark_spec.md  — full CANB spec (task schema, submission schema, scoring)
  5. report/aeas_paper.tex     — new paper skeleton you are implementing the infrastructure for
  6. src/aeas/*.py             — existing AEAS implementation you will reuse and adapt
  7. scripts/run_search.py     — existing AEAS runner
  8. audit.md                  — historical critical review that motivated the reframing

GOAL
The repo currently runs a narrow experiment on cos(2*pi/n) for n in {7,11,13}. Convert it into the CANB benchmark framework described in report/benchmark_spec.md. AEAS becomes the reference method; the paper pivots from "we studied three polygons" to "we built a benchmark and ran six methods on it."

HARD CONSTRAINTS
- Do NOT delete results/ or report/archive/. They are historical record.
- Do NOT modify src/aeas/expr.py, canonicalize.py, evaluate.py, field_search.py, search.py, chebyshev.py beyond ADDING (not changing) public helpers. The existing AEAS behavior must stay bit-identical so old results remain reproducible. If you need new behavior, add a new module.
- Do NOT introduce new heavy dependencies for v0.1 beyond: mpmath (already used), sympy, numpy, pytest, jsonschema. No PySR, no fpylll, no Anthropic SDK, no torch, no Ollama client yet — those come in later weeks.
- Python >= 3.11. Match existing style (black-default, type hints where present). Respect pyproject.toml.
- All randomness must be seeded. No wall-clock-dependent behavior in the benchmark generator or scorer.
- Never commit. Leave everything as uncommitted working-tree changes unless the user asks for a commit.

DELIVERABLES (in order — do not skip; do not reorder)

D1. Schema files under benchmark/
    D1.1. Create benchmark/schema/task.schema.json (JSON Schema draft-07) matching benchmark_spec.md §2.
    D1.2. Create benchmark/schema/submission.schema.json matching §4.
    D1.3. Create benchmark/schema/ast.schema.json for the restricted AST grammar in §4 (op in {CONST, NEG, INV, SQRT, ADD, SUB, MUL, DIV}, CONST.value is a "p/q" rational string, ADD/SUB/MUL/DIV/ take two args, NEG/INV/SQRT take one).
    D1.4. Add tests/test_schemas.py that loads each schema and validates one handcrafted positive and one handcrafted negative example per schema.

D2. AST serialization helpers
    D2.1. Create src/aeas/ast_io.py with:
          - expr_to_ast(expr)      — convert aeas.expr.Expression to dict per ast.schema.json
          - ast_to_expr(ast_dict)  — inverse; raise AstValidationError on invalid input
          - canonicalize_ast(ast)  — round-trip through src/aeas/canonicalize.py
    D2.2. Tests in tests/test_ast_io.py: round-trip on a library of 20 hand-written expressions including nested sqrt, division, negation; malformed cases raise correctly.

D3. Benchmark generator
    D3.1. Create scripts/generate_benchmark.py with CLI:
          --version X.Y --seed N --split {canb-poly,canb-trig,canb-transcend,all}
          --out benchmark/tasks
    D3.2. Implement three families for v0.1:
          - canb-poly: cos(2*pi/n) for non-Gauss-Wantzel n in [7, 200].
              Gauss-Wantzel test: n is GW iff n = 2^k * product(distinct Fermat primes {3,5,17,257,65537}). Exclude those.
          - canb-trig: sin(p*pi/q), tan(p*pi/q) for q non-Gauss-Wantzel in [7, 40], p in [1, q-1] reduced coprime, kept if target in (-1, 1) for sin and (-10, 10) for tan. Cap ~50 tasks; stable ordering by (q, p, fn).
          - canb-transcend: {pi, e, ln(2), euler_gamma, apery_zeta_3}. Use mpmath at 1100 dps for reference values, truncate to 1000-digit decimal string.
    D3.3. Each task JSON emitted per benchmark_spec.md §2. Include a deterministic id like canb-poly-n7, canb-trig-sin-p1-q7, canb-transcend-pi.
    D3.4. After all tasks generated, emit benchmark/MANIFEST.json with per-task SHA256 of the task file, the generator version, seed, and timestamp. Timestamp may be fixed to a constant if --deterministic is passed; implement that flag.
    D3.5. Running the generator twice with same args must produce byte-identical output. Assert this in tests/test_generator_deterministic.py by running the generator into two temp dirs and diffing.

D4. AEAS CANB adapter
    D4.1. Create src/aeas/canb_adapter.py exposing solve(task: dict, budget: dict) -> dict.
          - Parse target_spec; compute floating-point target and high-precision mpf target.
          - Map budget to existing AEAS knobs (walltime -> time budget gate; memory -> cap beam_width and max_height if needed; max_evaluations -> hard cap on mpmath calls).
          - Run field-first search via the existing src/aeas/field_search.py API.
          - Pick best candidate by (error, node_count, string) key.
          - Return a dict validated against submission.schema.json, including canonical AST (use src/aeas/ast_io.py).
    D4.2. Walltime enforcement: use signal.alarm-style cooperative check or a thread-polling flag inside field_search (whichever is least intrusive). Must stop work at budget.walltime_sec +/- 1s.
    D4.3. Tests: tests/test_canb_adapter.py runs solve() on 3 synthetic tasks (pi, cos(2pi/7), 1/2), verifies output passes schema validation and error is finite.

D5. Harness — runner
    D5.1. Create scripts/run_benchmark.py with CLI:
          --method <name> --split <name> --tasks-dir benchmark/tasks
          --out benchmark/submissions/<method>/<version>
          --budget '<json>' (default: {"walltime_sec":60, "memory_mb":2048, "max_evaluations":null})
          --resume (skip tasks already submitted)
          --n-parallel K (process-pool; default 1)
    D5.2. Load method via a registry in src/aeas/methods.py mapping name -> callable. Initial registrations: "aeas" -> aeas.canb_adapter.solve; "cf" -> (stub raising NotImplementedError for now). Stubs document that Week-2 baselines fill them in.
    D5.3. For each task: call solve, capture wall clock + peak rss via resource.getrusage, write submission JSON.
    D5.4. Tests: tests/test_runner_smoke.py runs "aeas" on canb-transcend (5 tasks, small budget) end-to-end and checks output files validate.

D6. Harness — scorer
    D6.1. Create scripts/score_benchmark.py:
          --method <name> --split <name>
          --submissions-dir benchmark/submissions/<method>/<version>
          --tasks-dir benchmark/tasks
          --out benchmark/scores/<method>.csv
    D6.2. For each submission: re-evaluate expression at 1000 dps via mpmath (DO NOT trust self-reported error), compute canonical node count, walltime already recorded. Compute per-task Pareto hypervolume per benchmark_spec.md §5.
    D6.3. Secondary metrics per §5: BestError, WinRate@60s (requires comparing against other methods — if only one method scored, emit NaN gracefully), ExactRate, SizeAtBest.
    D6.4. Emit one CSV row per task + a summary footer row (or separate summary JSON).
    D6.5. Tests: tests/test_scorer.py feeds 3 synthetic submissions + tasks, checks HV values monotonic in the obvious way.

D7. CLI integration + documentation
    D7.1. Update README.md Quick-start block: show the new end-to-end pipeline.
          Example:
            python scripts/generate_benchmark.py --version 0.1 --seed 20260420 --split all
            python scripts/run_benchmark.py --method aeas --split canb-transcend
            python scripts/score_benchmark.py --method aeas --split canb-transcend
    D7.2. Update benchmark/README.md with real command examples (remove TODO placeholders).
    D7.3. Add "CANB harness" section to AGENTS.md explaining the new layout.

D8. First end-to-end smoke on canb-transcend
    D8.1. Actually run:
            python scripts/generate_benchmark.py --version 0.1 --seed 20260420 --split canb-transcend --deterministic
            python scripts/run_benchmark.py --method aeas --split canb-transcend --budget '{"walltime_sec":30}'
            python scripts/score_benchmark.py --method aeas --split canb-transcend
          All three must exit 0.
    D8.2. Inspect benchmark/scores/aeas.csv and confirm non-NaN scores for at least 3 of 5 transcendental tasks (AEAS should find decent rational/low-depth approximations even for pi and e).

D9. Continued-fractions baseline (Week 2 head-start)
    D9.1. Create src/aeas/baselines/__init__.py and src/aeas/baselines/cf.py.
    D9.2. cf.solve(task, budget) = best rational p/q for denominator q <= H_max (default 200) via continued-fraction convergents. Emit as CONST("p/q") AST.
    D9.3. Register "cf" in methods.py.
    D9.4. Run the smoke pipeline for cf on canb-transcend and canb-poly; record scores. Score floor expected: CF only beats AEAS at depth 0 when AEAS is budget-starved.

TEST DISCIPLINE
- Every deliverable D1..D9 has corresponding tests under tests/.
- After each D_i, run: pytest tests/ -x -q
- If tests regress on EXISTING files (test_canonicalize, test_evaluate, test_expr, test_field_search, test_chebyshev), STOP and report. Do not suppress or skip.

STOP CRITERIA — end the run when either:
  (A) D1 through D9 complete, all tests green, smoke pipeline D8 + cf baseline ran successfully. Emit a final STATUS.md under report/ summarizing what was built, test counts, and any deviations from this prompt.
  (B) Two consecutive deliverables fail despite >= 3 repair attempts each. Emit STATUS.md summarizing progress and blockers.

ANTI-GOALS — do not do any of these, even if tempted:
- Do not implement PSLQ, LLL, PySR, LLM, or MCTS baselines. Out of scope for this run; separate future codex runs.
- Do not generate canb-algdeg, canb-nestedref, or canb-rand families. v0.2.
- Do not refactor existing AEAS internals for "cleanliness." They work; leave them.
- Do not write new documentation beyond what is specified.
- Do not write emojis in files.
- Do not add license headers unless the existing files have them (none do).
- Do not create Git commits or branches.

SELF-VERIFICATION BEFORE STOP
Before emitting STATUS.md, run and record output of:
  - pytest tests/ -q --tb=line
  - python scripts/generate_benchmark.py --version 0.1 --seed 20260420 --split all --deterministic --out /tmp/canb_test_tasks
  - diff -r benchmark/tasks /tmp/canb_test_tasks   (must be empty)
  - python scripts/run_benchmark.py --method aeas --split canb-transcend --budget '{"walltime_sec":10}' --out /tmp/canb_test_subs
  - python scripts/score_benchmark.py --method aeas --split canb-transcend --submissions-dir /tmp/canb_test_subs --out /tmp/canb_test_scores.csv
  - cat /tmp/canb_test_scores.csv

Attach the tails of each in STATUS.md.

STYLE AND TONE
- Terse code. Type-hint new public functions.
- Docstrings only where behavior is non-obvious.
- No commentary in code about "why I did this."
- Error messages should be useful: include offending values.
- Print progress on long-running commands (tqdm is fine; it is a transitive dep).

Begin. Read the background files first. Announce your plan before writing any code. Then execute D1..D9 in order.
```

---

## How to invoke

```bash
codex exec --sandbox workspace-write \
  --skip-git-repo-check \
  --cd /Users/bato/MyProjects/automated-euclidean-approximation-system \
  --model gpt-5-codex  \
  "$(cat report/CODEX_MASTER_PROMPT.md | sed -n '/^```$/,/^```$/p' | sed '1d;$d')"
```

Or open codex TUI and paste the fenced block above.

## What comes out

- `benchmark/schema/*.json` — three JSON schemas
- `benchmark/tasks/` — ~125 task files across 3 families
- `benchmark/submissions/aeas/<version>/*.json` — AEAS submissions on canb-transcend smoke
- `benchmark/submissions/cf/<version>/*.json` — CF baseline submissions
- `benchmark/scores/aeas.csv`, `cf.csv` — scored outputs
- `benchmark/MANIFEST.json` — task SHA256 index
- `scripts/generate_benchmark.py`, `run_benchmark.py`, `score_benchmark.py`
- `src/aeas/ast_io.py`, `canb_adapter.py`, `methods.py`, `baselines/cf.py`
- Tests for each of the above
- `report/STATUS.md` — end-of-run report

## After codex completes

Manually:
1. `git status` and review all new files.
2. Read `report/STATUS.md`.
3. If green: `git add -A && git commit -m "feat: CANB v0.1 harness + AEAS adapter + CF baseline"`.
4. Start Week 2 (PSLQ baseline) in a new codex run using this same pattern — write a dedicated shorter prompt pointing at the now-existing harness.
