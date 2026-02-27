# Automated Euclidean Approximation System (AEAS)

AEAS searches constructible-number approximations to `cos(2π/n)` for non-constructible polygon sizes (notably `n=7,11,13`).

## Canonical docs

- Agent/project instructions: `AGENTS.md`
- Reproducible runbook: `runs.md`
- Paper planning + handoff: `report/PLAN.md`
- Manuscript draft: `report/aeas_paper.tex`

## Quick start

```bash
micromamba create -f aeas-env.yml
micromamba activate aeas
pip install -e .

# one-command sequential rerun (core + visuals)
bash scripts/rerun_all.sh --purge-results
```

Optional experiment extensions:

```bash
# stronger robustness runs
bash scripts/rerun_all.sh --purge-results --extra-experiments

# parameter-justification sweeps
bash scripts/rerun_all.sh --purge-results --justification-experiments
```

## Core scripts

- `scripts/run_search.py`: run one search configuration
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
