# CANB v0.1 Experiments

This file is the human-readable experiment plan. `report/STATUS.md` is the
audit log of exact commands and tails.

## Research Question

Can AEAS find lower-error constructible-number approximations than cheap
baselines, and what cost does it pay in expression size and walltime?

The benchmark is not asking whether AEAS exactly recovers every target. For
many targets, exact recovery by constructible expressions is impossible or not
the point. The measured object is the best approximation found under a fixed
method budget.

## Targets

Primary evidence is `canb-poly`:

- 167 tasks of the form `cos(2*pi/n)`.
- `n` ranges from 7 to 200.
- Constructible Gauss-Wantzel cases are excluded.
- These targets are the natural fit for AEAS because the original system was
  built around constructible approximants to polygon constants.

Control evidence is `canb-transcend`:

- 5 tasks: `pi`, `e`, `ln(2)`, Euler gamma, and `zeta(3)`.
- These are sanity checks for the harness and baselines.
- They should not be treated as the main AEAS claim.

`canb-trig` exists in the v0.1 task set but has not yet been part of the Week-2
comparison run.

## Methods

`aeas`:

- Field-first constructible search.
- Outputs expressions over rationals using `+, -, *, /, sqrt`.
- Expected to improve numerical error at the cost of larger expressions and
  more walltime.

`cf`:

- Continued-fraction rational baseline.
- Outputs a single rational `p/q`.
- Expected to be very small and fast, but less accurate.

`pslq`:

- PSLQ baseline over low-degree square-root bases.
- If no relation is found, it emits a rational fallback and says so in
  `submission["notes"]`.
- The current Week-2 PSLQ implementation is a smoke baseline, not yet a strong
  symbolic competitor.

## Metrics

Primary metrics:

- `error`: absolute numerical error after scorer re-evaluation at high
  precision. Lower is better.
- `node_count`: canonical AEAS AST node count. Lower is smaller.
- `walltime_sec`: runner-captured walltime. Lower is faster.

Secondary metrics:

- `exact_rate`: fraction of tasks with error below the scorer exact threshold.
- `Cpath`: the score CSV summary hypervolume. This mixes error, size, and time,
  so it is useful for frontier accounting but should not replace the primary
  table.

For scientific interpretation, report the primary metrics as a table before
discussing hypervolume.

## Current Week-2 Results

`canb-poly`, 167 tasks:

| method | median error | median nodes | median walltime | exact rate | Cpath |
|---|---:|---:|---:|---:|---:|
| aeas | 1.591016214202e-8 | 11 | 1.294890708 s | 0 | 0.0828373977413 |
| cf | 7.806906464281e-4 | 1 | 0.000327415997162 s | 0 | 0.114793178885 |
| pslq | 7.806906464281e-4 | 1 | 0.329378916998 s | 0 | 0.0666132337621 |

Interpretation:

- AEAS found lower-error approximants on all 167 `canb-poly` tasks compared
  with CF.
- CF and PSLQ are much smaller and faster because they mostly emit rationals.
- On the three-axis frontier `(error, node_count, walltime_sec)`, AEAS and CF
  are non-dominated: AEAS wins on error, CF wins on size and time.
- The honest claim is not "AEAS wins"; it is "AEAS occupies the lower-error
  region of the frontier."

`canb-transcend`, 5 tasks:

| method | median log10 error | median nodes | Cpath |
|---|---:|---:|---:|
| aeas | -7.46079426507 | 11 | 0.0780777201949 |
| cf | -4.69664286885 | 1 | 0.167712638412 |
| pslq | -4.69664286885 | 1 | 0.0977017047701 |

Interpretation:

- This split is a harness/control check.
- It should not carry the paper's main claim.

The current PSLQ smoke recorded `relation_found=false` for all 5
`canb-transcend` tasks and all 167 `canb-poly` tasks. That means these PSLQ
numbers are rational-fallback numbers, not evidence that PSLQ found useful
square-root relations.

## Reproducing The Compact Tables

Use `scripts/compare_methods.py` after scoring each method:

```bash
/Users/bato/micromamba/envs/aeas/bin/python scripts/compare_methods.py --split canb-poly --out benchmark/runs/comparison-canb-poly.csv --markdown
/Users/bato/micromamba/envs/aeas/bin/python scripts/compare_methods.py --split canb-transcend --out benchmark/runs/comparison-canb-transcend.csv --markdown
```

The script discovers score CSVs under `benchmark/runs/*/score.csv` and
`benchmark/scores/*.csv`, then emits one row per method with median error,
median size, median walltime, exact rate, and `Cpath`.

## Expected Outcome

The expected v0.1 result is:

> AEAS substantially reduces approximation error on `canb-poly`, while paying
> higher walltime and expression-size cost than rational baselines.

That outcome is useful if the paper is framed as a benchmark/frontier study,
not as a universal method victory.

## Known Weaknesses

- The PSLQ baseline is currently weak. It needs richer basis selection and
  clearer reporting of genuine relations versus rational fallback.
- Hypervolume compresses several tradeoffs into one number. It can hide the
  main result unless shown next to median error, size, and walltime.
- The AEAS q-height cap exposed in Week 2 can lower the adapter's effective
  height, but the protected core still contains `q_height = min(max_height, 14)`.
  Raising that cap requires an explicit core change.
- `canb-trig` still needs matched runs before v0.1 claims generality beyond
  polygon cosine tasks.

## Next Experiments

1. Run matched-budget sweeps for `aeas`, `cf`, and `pslq` on `canb-poly` and
   `canb-trig`.
2. Decide whether to make the internal AEAS q-height cap a true field-search
   parameter.
3. Strengthen PSLQ with richer basis selection so it becomes a real symbolic
   baseline instead of mostly a rational fallback.
