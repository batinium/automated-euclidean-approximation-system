# AEAS + CANB

**AEAS** — a field-first search for bounded-height constructible approximations to arbitrary real targets (nested-square-root expressions over `Q`).

**CANB** — the Constructible Approximation Number Benchmark: standardized tasks + submission schema + Pareto scoring for comparing methods on this problem. AEAS is the reference method. See `report/benchmark_spec.md`.

The original `cos(2π/n)` experiments for `n ∈ {7, 11, 13}` are preserved under `results/` and `report/archive/` and become the `canb-poly` subset in the new benchmark.

## Canonical docs

- Agent/project instructions: `AGENTS.md`
- Reproducible runbook (legacy AEAS direct invocation): `runs.md`
- Track A plan (benchmark reframing): `report/PLAN.md`
- Executable roadmap: `report/ROADMAP.md`
- Benchmark spec: `report/benchmark_spec.md`
- Manuscript draft (benchmark + method paper): `report/aeas_paper.tex`
- Publication audit: `audit.md`
- Archived v1 (cos-only paper): `report/archive/`

## Quick start

```bash
micromamba create -f aeas-env.yml
micromamba activate aeas
pip install -e ".[dev]"

# CANB end-to-end smoke
python scripts/generate_benchmark.py --version 0.1 --seed 20260420 --split all --deterministic
python scripts/run_benchmark.py --method aeas --split canb-transcend
python scripts/score_benchmark.py --method aeas --split canb-transcend
```

Legacy AEAS direct runs are still available:

```bash
# one-command sequential rerun (core + visuals)
bash scripts/rerun_all.sh --purge-results

# parameter-justification sweeps for the old cos-only study
bash scripts/rerun_all.sh --purge-results --justification-experiments
```

## Core scripts

- `scripts/run_search.py`: run one search configuration
- `scripts/generate_benchmark.py`: generate CANB task JSON + manifest
- `scripts/run_benchmark.py`: run a registered method over one CANB split
- `scripts/score_benchmark.py`: re-evaluate submissions and emit score CSV
- `scripts/plot_results.py`: generate per-run and multi-run plots
- `scripts/analyse_scaling.py`: generate paper analysis tables/figures
- `scripts/visualize_search.py`: architecture/tree/heatmap visuals
- `scripts/rerun_all.sh`: sequential end-to-end automation

## Key outputs

- Per-run artifacts: `results/<run_name>/`
- Aggregated grid summary: `results/multi_run_summary.csv`
- Paper-ready analysis artifacts: `results/analysis/`
  - `field_vs_beam_baseline_table.csv`
  - `field_vs_beam_bestof_table.csv`
  - `height_scaling_table.csv`
  - `depth_scaling_table.csv`
  - `saturation_table.csv`

## Notes

- Main RQ2 claim should use `field_vs_beam_baseline_table.csv`.
- `field_vs_beam_bestof_table.csv` is robustness context, not baseline claim.
- Run tests with `pytest tests/ -v`.
