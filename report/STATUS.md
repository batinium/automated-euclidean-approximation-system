# CANB Harness Status

Date: 2026-04-20

## Summary

D1 through D9 are complete.

- Added JSON Schemas for tasks, submissions, and `aeas-ast-v1` under `benchmark/schema/`.
- Added AST serialization helpers in `src/aeas/ast_io.py`.
- Added deterministic v0.1 task generation in `scripts/generate_benchmark.py`.
- Added shared CANB target helpers in `src/aeas/canb_targets.py`.
- Added AEAS harness adapter in `src/aeas/canb_adapter.py` with subprocess walltime enforcement and evaluation counting.
- Added method registry in `src/aeas/methods.py`.
- Added benchmark runner and scorer scripts.
- Added scoring utilities in `src/aeas/scoring.py`.
- Added continued-fractions baseline in `src/aeas/baselines/cf.py`.
- Updated README, benchmark README, and AGENTS.md with CANB harness usage.
- Generated v0.1 tasks under `benchmark/tasks/` and manifest under `benchmark/MANIFEST.json`.
- Ran AEAS smoke on `canb-transcend`.
- Ran CF smoke on `canb-transcend` and `canb-poly`.

No legacy AEAS core files were modified: `expr.py`, `canonicalize.py`,
`evaluate.py`, `field_search.py`, `search.py`, and `chebyshev.py` are unchanged.
Historical `results/` and `report/archive/` were not deleted.

## Deviations

- The shell did not have `python` or `pytest` on PATH. Verification used
  `/Users/bato/micromamba/envs/aeas/bin/python` and
  `/Users/bato/micromamba/envs/aeas/bin/python -m pytest`.
- The active `aeas` environment did not have the external `jsonschema` package
  installed. `pyproject.toml` now declares it, and `src/aeas/schema_validation.py`
  uses it when available with a local fallback for this repository's draft-07
  schema subset.
- Cleanup with `rm -rf /tmp/...` was blocked by sandbox policy, so no cleanup
  command was used. The requested `/tmp` verification paths did not exist before
  the final run.

## Test Count

Final suite: 143 passed, 6 warnings.

Warnings are from `mpmath.polyroots` deprecation for descending polynomial
coefficient order in synthetic `root_of_polynomial` tests.

## D8 AEAS Smoke

`benchmark/scores/aeas.csv` contained non-NaN per-task hypervolume scores for
all 5 transcendental tasks. Summary score from the 30s smoke:

```text
summary,SUMMARY,,aeas,,,,,,0.0780777201949,,-7.46079426507,nan,0,11,
```

## D9 CF Smoke

CF transcend summary:

```text
summary,SUMMARY,,cf,,,,,,0.167712638412,,-4.69664286885,nan,0,1,
```

CF poly summary:

```text
summary,SUMMARY,,cf,,,,,,0.114793178885,,-3.10752102395,nan,0,1,
```

## Final Verification

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/ -q --tb=line
```

Tail:

```text
........................................................................ [ 50%]
.......................................................................  [100%]
143 passed, 6 warnings in 1.93s
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/generate_benchmark.py --version 0.1 --seed 20260420 --split all --deterministic --out /tmp/canb_test_tasks
```

Tail:

```text
wrote 222 tasks to /tmp/canb_test_tasks
wrote manifest to /tmp/MANIFEST.json
```

Command:

```text
diff -r benchmark/tasks /tmp/canb_test_tasks
```

Tail:

```text
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/run_benchmark.py --method aeas --split canb-transcend --budget '{"walltime_sec":10}' --out /tmp/canb_test_subs
```

Tail:

```text
wrote /tmp/canb_test_subs/canb-transcend-apery-zeta-3.json
wrote /tmp/canb_test_subs/canb-transcend-e.json
wrote /tmp/canb_test_subs/canb-transcend-euler-gamma.json
wrote /tmp/canb_test_subs/canb-transcend-ln2.json
wrote /tmp/canb_test_subs/canb-transcend-pi.json
completed 5 tasks for method=aeas
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/score_benchmark.py --method aeas --split canb-transcend --submissions-dir /tmp/canb_test_subs --out /tmp/canb_test_scores.csv
```

Tail:

```text
wrote /tmp/canb_test_scores.csv
```

Command:

```text
cat /tmp/canb_test_scores.csv
```

Output:

```text
row_type,task_id,family,method,status,error,log10_error,node_count,walltime_sec,hypervolume,exact,best_error_median_log10,win_rate_60s,exact_rate,size_at_best_median,expression
task,canb-transcend-apery-zeta-3,canb-transcend,aeas,success,3.63414581689889075e-7,-6.43959765099,11,0.182388792018,0.0873309181251,False,,,,,(((25/8) * sqrt((((-3/8) * sqrt(11)) + (22/9)))) + (-20/9))
task,canb-transcend-e,canb-transcend,aeas,success,3.91201988025974935e-7,-6.40759894686,11,0.189394249988,0.0865165476584,False,,,,,(((7/4) * sqrt((((9/5) * sqrt(3)) + (-2/5)))) + (-1/6))
task,canb-transcend-euler-gamma,canb-transcend,aeas,success,6.54535454076528648e-8,-7.18406682414,11,0.192130167008,0.0968382529793,False,,,,,(((-12/7) * sqrt((((8/9) * sqrt(11)) + (-19/8)))) + (15/8))
task,canb-transcend-ln2,canb-transcend,aeas,success,2.19608473656346506e-7,-6.65835090652,11,0.193475541979,0.0896786322,False,,,,,(((-11/8) * sqrt((((8/9) * sqrt(5)) + (-13/10)))) + (11/6))
task,canb-transcend-pi,canb-transcend,aeas,success,5.43494458894525871e-7,-6.26480487933,11,0.189923208993,0.0845609936578,False,,,,,(((5/7) * sqrt((((12/5) * sqrt(5)) + (-20/9)))) + (15/8))
summary,SUMMARY,,aeas,,,,,,0.0889850689241,,-6.43959765099,nan,0,11,
```

## Week-2 W1 — AEAS x canb-poly vs CF

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/run_benchmark.py --method aeas --split canb-poly --out benchmark/runs/aeas-canb-poly/submissions
```

Tail:

```text
wrote benchmark/runs/aeas-canb-poly/submissions/canb-poly-n98.json
wrote benchmark/runs/aeas-canb-poly/submissions/canb-poly-n99.json
completed 167 tasks for method=aeas
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/score_benchmark.py --method aeas --split canb-poly --submissions-dir benchmark/runs/aeas-canb-poly/submissions --out benchmark/runs/aeas-canb-poly/score.csv
```

Tail:

```text
wrote benchmark/runs/aeas-canb-poly/score.csv
```

Per-family aggregate, `canb-poly`:

```text
method  tasks  median_error       exact_rate  median_walltime_sec  total_walltime_sec  mean_hypervolume
aeas    167    1.591016214202e-8  0           1.294890708          216.697012415       0.0828373977413
cf      167    7.806906464281e-4  0           0.000327415997162    0.0622614568856     0.114793178885
```

Frontier dominance on `(error, node_count, walltime_sec)`, lower is better:

```text
AEAS dominates: 0
CF dominates: 0
Tie: 0
Non-dominated: 167
AEAS lower-error count: 167
CF lower-error count: 0
```

Score CSV path: `benchmark/runs/aeas-canb-poly/score.csv`.

## Week-2 W2 — PSLQ baseline

Implemented `src/aeas/baselines/pslq.py`, registered method id `pslq` in
`src/aeas/methods.py`, and added `tests/test_pslq_baseline.py`.

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/ -q
```

Tail:

```text
146 passed, 11 warnings in 2.00s
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/run_benchmark.py --method pslq --split canb-transcend --out benchmark/runs/pslq-canb-transcend/submissions
```

Tail:

```text
wrote benchmark/runs/pslq-canb-transcend/submissions/canb-transcend-apery-zeta-3.json
wrote benchmark/runs/pslq-canb-transcend/submissions/canb-transcend-e.json
wrote benchmark/runs/pslq-canb-transcend/submissions/canb-transcend-euler-gamma.json
wrote benchmark/runs/pslq-canb-transcend/submissions/canb-transcend-ln2.json
wrote benchmark/runs/pslq-canb-transcend/submissions/canb-transcend-pi.json
completed 5 tasks for method=pslq
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/score_benchmark.py --method pslq --split canb-transcend --submissions-dir benchmark/runs/pslq-canb-transcend/submissions --out benchmark/runs/pslq-canb-transcend/score.csv
```

Tail:

```text
wrote benchmark/runs/pslq-canb-transcend/score.csv
summary,SUMMARY,,pslq,,,,,,0.0972881582393,,-4.69664286885,nan,0,1,
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/run_benchmark.py --method pslq --split canb-poly --out benchmark/runs/pslq-canb-poly/submissions
```

Tail:

```text
wrote benchmark/runs/pslq-canb-poly/submissions/canb-poly-n97.json
wrote benchmark/runs/pslq-canb-poly/submissions/canb-poly-n98.json
wrote benchmark/runs/pslq-canb-poly/submissions/canb-poly-n99.json
completed 167 tasks for method=pslq
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/score_benchmark.py --method pslq --split canb-poly --submissions-dir benchmark/runs/pslq-canb-poly/submissions --out benchmark/runs/pslq-canb-poly/score.csv
```

Tail:

```text
wrote benchmark/runs/pslq-canb-poly/score.csv
summary,SUMMARY,,pslq,,,,,,0.0665958787064,,-3.10752102395,nan,0,1,
```

## Week-2 W3 — AEAS q-height cap knob

The hard-coded depth-2 field-search cap is in protected core at
`src/aeas/field_search.py`:

```text
q_height = min(max_height, 14)
```

Because protected legacy core files are not to be modified, the exposed knob is
adapter-side: `scripts/run_benchmark.py --aeas-q-height-cap N` is accepted only
with `--method aeas` and is forwarded as `budget["aeas_q_height_cap"]`. The
adapter lowers the effective `max_height` for depth >= 2 when this key is set.
The default is unset, preserving the previous AEAS path.

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/test_canb_adapter.py tests/test_runner_smoke.py -q
```

Tail:

```text
7 passed, 5 warnings in 0.61s
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/run_benchmark.py --method aeas --split canb-transcend --budget '{"walltime_sec":30}' --out benchmark/runs/aeas-transcend-default-check/submissions
```

Tail:

```text
wrote benchmark/runs/aeas-transcend-default-check/submissions/canb-transcend-apery-zeta-3.json
wrote benchmark/runs/aeas-transcend-default-check/submissions/canb-transcend-e.json
wrote benchmark/runs/aeas-transcend-default-check/submissions/canb-transcend-euler-gamma.json
wrote benchmark/runs/aeas-transcend-default-check/submissions/canb-transcend-ln2.json
wrote benchmark/runs/aeas-transcend-default-check/submissions/canb-transcend-pi.json
completed 5 tasks for method=aeas
```

Command:

```text
diff -r benchmark/submissions/aeas/0.1 benchmark/runs/aeas-transcend-default-check/submissions
```

Tail:

```text
Only metrics.walltime_sec and metrics.peak_memory_mb differed for the 5 files.
These fields are captured by the runner and were already nondeterministic.
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python - <<'PY'
import json
from pathlib import Path

left = Path('benchmark/submissions/aeas/0.1')
right = Path('benchmark/runs/aeas-transcend-default-check/submissions')
changed = []
for path in sorted(left.glob('*.json')):
    a = json.loads(path.read_text())
    b = json.loads((right / path.name).read_text())
    for obj in (a, b):
        obj['metrics']['walltime_sec'] = '<runtime>'
        obj['metrics']['peak_memory_mb'] = '<rss>'
    if a != b:
        changed.append(path.name)
if changed:
    raise SystemExit('normalized differences: ' + ', '.join(changed))
print('normalized AEAS canb-transcend default outputs match existing run')
PY
```

Tail:

```text
normalized AEAS canb-transcend default outputs match existing run
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/ -q
```

Tail:

```text
149 passed, 14 warnings in 2.11s
```

## Week-2 Closeout

Completed deliverables:

- W1: Ran AEAS on all 167 `canb-poly` tasks under
  `benchmark/runs/aeas-canb-poly/submissions`, scored it at
  `benchmark/runs/aeas-canb-poly/score.csv`, and compared it against CF.
- W2: Added PSLQ baseline at `src/aeas/baselines/pslq.py`, registered method
  id `pslq`, added PSLQ tests, and smoke-ran/scored PSLQ on
  `canb-transcend` and `canb-poly`.
- W3: Added `scripts/run_benchmark.py --aeas-q-height-cap N`, forwarded only
  for AEAS, and added adapter/runner tests for the new knob.

Protected legacy AEAS core files were not modified:
`src/aeas/expr.py`, `canonicalize.py`, `evaluate.py`, `field_search.py`,
`search.py`, and `chebyshev.py`.

Final verification command:

```text
/Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/ -q
```

Tail:

```text
149 passed, 14 warnings in 2.13s
```

Task determinism command:

```text
/Users/bato/micromamba/envs/aeas/bin/python - <<'PY'
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

root = Path.cwd()
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / 'tasks'
    result = subprocess.run(
        [
            '/Users/bato/micromamba/envs/aeas/bin/python',
            'scripts/generate_benchmark.py',
            '--version',
            '0.1',
            '--seed',
            '20260420',
            '--split',
            'all',
            '--deterministic',
            '--out',
            str(out),
        ],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    expected_files = sorted(p.relative_to(root / 'benchmark/tasks') for p in (root / 'benchmark/tasks').rglob('*.json'))
    actual_files = sorted(p.relative_to(out) for p in out.rglob('*.json'))
    if expected_files != actual_files:
        raise SystemExit('task file list differs')
    diffs = [str(rel) for rel in expected_files if (root / 'benchmark/tasks' / rel).read_bytes() != (out / rel).read_bytes()]
    if diffs:
        raise SystemExit('task bytes differ: ' + ', '.join(diffs[:10]))
    print(result.stdout.strip())
    print(f'byte_equal_tasks={len(expected_files)}')
PY
```

Tail:

```text
wrote 222 tasks to /var/folders/4b/tp113nxn78bdvdmh6cgfvwl40000gn/T/tmpog55asa0/tasks
wrote manifest to /var/folders/4b/tp113nxn78bdvdmh6cgfvwl40000gn/T/tmpog55asa0/MANIFEST.json
byte_equal_tasks=222
```

Score summary rows:

```text
aeas canb-poly: summary,SUMMARY,,aeas,,,,,,0.0828373977413,,-7.79832539439,nan,0,11,
pslq canb-transcend: summary,SUMMARY,,pslq,,,,,,0.0972881582393,,-4.69664286885,nan,0,1,
pslq canb-poly: summary,SUMMARY,,pslq,,,,,,0.0665958787064,,-3.10752102395,nan,0,1,
```

Environment workarounds:

- Used `/Users/bato/micromamba/envs/aeas/bin/python` for all Python and pytest
  invocations because plain `python`/`pytest` are not assumed on PATH.
- Used `tempfile.TemporaryDirectory()` for task determinism scratch output,
  avoiding blocked manual `/tmp` cleanup.
- External `jsonschema` was not required; the repository fallback validator
  continued to cover the schema checks.

Notes:

- Raw `diff -r` between the existing AEAS transcend smoke and a fresh no-flag
  default run differed only in runner-captured `metrics.walltime_sec` and
  `metrics.peak_memory_mb`. After normalizing those two nondeterministic fields,
  all AEAS default outputs matched the existing run.
- The field-search internal `q_height = min(max_height, 14)` remains in
  protected `src/aeas/field_search.py`. The new adapter knob can lower the
  effective cap, but raising it above the protected core limit remains a
  Week-4/core-change item.

Next steps:

- Decide whether Week 4 should modify protected `field_search.py` to replace
  the internal `14` with a true parameter.
- Add a combined leaderboard/frontier scorer so pairwise method comparisons do
  not require ad hoc CSV analysis.
- Run matched-budget sweeps for `aeas`, `cf`, and `pslq` across all v0.1
  splits once the q-height policy is finalized.

## Experiment Narrative Cleanup

Added `report/EXPERIMENTS.md` to separate the scientific experiment narrative
from this audit log. The document states the research question, target splits,
method roles, primary metrics, current result tables, expected outcome, and
known weaknesses.

Added `scripts/compare_methods.py` and `tests/test_compare_methods.py`.

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/compare_methods.py --split canb-poly --out benchmark/runs/comparison-canb-poly.csv --markdown
```

Output:

```text
| method | tasks | median_error | median_nodes | median_walltime_sec | exact_rate | Cpath |
|---|---:|---:|---:|---:|---:|---:|
| aeas | 167 | 1.5910162142e-08 | 11 | 1.294890708 | 0 | 0.0828373977413 |
| cf | 167 | 0.000780690646428 | 1 | 0.000327415997162 | 0 | 0.114793178885 |
| pslq | 167 | 0.000780690646428 | 1 | 0.329378916998 | 0 | 0.0666132337621 |
```

Command:

```text
/Users/bato/micromamba/envs/aeas/bin/python scripts/compare_methods.py --split canb-transcend --out benchmark/runs/comparison-canb-transcend.csv --markdown
```

Output:

```text
| method | tasks | median_error | median_nodes | median_walltime_sec | exact_rate | Cpath |
|---|---:|---:|---:|---:|---:|---:|
| aeas | 5 | 3.46103295803e-08 | 11 | 1.26522879201 | 0 | 0.0780777201949 |
| cf | 5 | 2.01074561907e-05 | 1 | 0.000439416995505 | 0 | 0.167712638412 |
| pslq | 5 | 2.01074561907e-05 | 1 | 0.324944791006 | 0 | 0.0977017047701 |
```

Updated PSLQ notes to begin with `relation_found=true;` or
`relation_found=false;`. Current smoke artifacts report:

```text
pslq-canb-transcend {'relation_found=true': 0, 'relation_found=false': 5}
pslq-canb-poly {'relation_found=true': 0, 'relation_found=false': 167}
```

Final verification command:

```text
/Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/ -q
```

Tail:

```text
150 passed, 14 warnings in 2.20s
```
