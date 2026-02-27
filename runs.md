# AEAS full rerun playbook

Use this file to rerun all paper experiments from a clean `results/` directory.

## 0) Environment

```bash
# from repo root
micromamba activate aeas
pip install -e .
```

## One-command sequential run

```bash
# archive existing results/ first, then run everything end-to-end
bash scripts/rerun_all.sh --purge-results

# if you want to skip visualize_search.py:
# bash scripts/rerun_all.sh --purge-results --no-visuals

# include extra robustness experiments too:
# bash scripts/rerun_all.sh --purge-results --extra-experiments

# include compact parameter-justification experiments too:
# bash scripts/rerun_all.sh --purge-results --justification-experiments

# run everything (core + extras + justification):
# bash scripts/rerun_all.sh --purge-results --extra-experiments --justification-experiments
```

## 1) Optional backup + purge `results/`

```bash
# optional: archive current results before purge
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p results_archive
mv results "results_archive/results_${TS}" 2>/dev/null || true
mkdir -p results

# if you prefer hard purge instead of move/archive:
# rm -rf results/*
```

## 2) RQ2 baseline: field vs beam

```bash
# Beam search baseline
python3 scripts/run_search.py \
  --mode beam \
  --n 7 11 13 \
  --max_depth 3 \
  --max_nodes 15 \
  --beam_width 2000 \
  --dps 80 \
  --run_name "beam_n7-11-13_d3_nodes15_bw2000"

# Field search baseline
python3 scripts/run_search.py \
  --mode field \
  --n 7 11 13 \
  --max_depth 3 \
  --max_height 20 \
  --max_radicand 30 \
  --beam_width 2000 \
  --dps 80 \
  --run_name "field_n7-11-13_d3_h20_r30_bw2000"
```

## 3) RQ1 height scaling sweep (depth=2)

```bash
for H in 8 12 16 24 32 48; do
  python3 scripts/run_search.py \
    --mode field \
    --n 7 11 13 \
    --max_depth 2 \
    --max_height "$H" \
    --max_radicand 30 \
    --beam_width 2000 \
    --dps 80 \
    --run_name "field_n7-11-13_d2_h${H}_r30_bw2000"
done
```

## 4) RQ1 depth scaling sweep (height=32)

```bash
for D in 0 1 2 3 4; do
  python3 scripts/run_search.py \
    --mode field \
    --n 7 11 13 \
    --max_depth "$D" \
    --max_height 32 \
    --max_radicand 30 \
    --beam_width 2000 \
    --dps 80 \
    --run_name "field_n7-11-13_d${D}_h32_r30_bw2000"
done
```

## 5) Saturation control run (height=64)

```bash
python3 scripts/run_search.py \
  --mode field \
  --n 7 11 13 \
  --max_depth 4 \
  --max_height 64 \
  --max_radicand 30 \
  --beam_width 2000 \
  --dps 80 \
  --run_name "field_n7-11-13_d4_h64_r30_bw2000"
```

## 6) Regenerate plots + aggregated analysis

```bash
# per-run figures for every run
python3 scripts/plot_results.py --root results --all-runs

# cross-run grid + multi_run_summary.csv
python3 scripts/plot_results.py --root results --multi-run-grid

# paper analysis tables/figures into results/analysis/
python3 scripts/analyse_scaling.py

# optional paper visuals (architecture/trees/heatmaps)
python3 scripts/visualize_search.py --root results --mode all --n 7 --depth 3 --rank 1 --m 2 --max-height 32
```

`scripts/analyse_scaling.py` now emits:
- `results/analysis/field_vs_beam_baseline_table.csv` (strict canonical baseline pair)
- `results/analysis/field_vs_beam_bestof_table.csv` (best-by-mode across all runs)
- `results/analysis/field_vs_beam_table.csv` (backward-compatible alias of baseline table)

## 7) Quick sanity checks

```bash
# expected run directories
ls -1 results | rg '^beam_n7-11-13_d3_nodes15_bw2000|^field_n7-11-13_d3_h20_r30_bw2000|^field_n7-11-13_d2_h(8|12|16|24|32|48)_r30_bw2000|^field_n7-11-13_d[0-4]_h32_r30_bw2000|^field_n7-11-13_d4_h64_r30_bw2000'

# expected analysis outputs
ls -1 results/analysis
```

## 8) Runtime expectations (rough)

- Beam baseline: ~1 minute
- Field baseline (`h=20`): ~5-10 minutes total for n=7,11,13 depending on machine
- Height sweep (6 runs): largest cost block
- Depth sweep (5 runs): moderate
- `h=64` run: usually the slowest single run

Total wall-clock depends heavily on CPU and whether `src/aeas/field_search.py` was modified (especially nested denominator limits).

## 9) Parameter-justification mini-suite (for report narrative)

If you need to justify fixed defaults (`beam_width=2000`, `max_radicand=30`, `dps=80`, etc.), run:

```bash
bash scripts/rerun_all.sh --justification-experiments
```

This adds compact sweeps:

- Field `beam_width` sensitivity:
  - `justif_field_bw1000_d3_h20_r30_dps80`
  - `justif_field_bw2000_d3_h20_r30_dps80`
  - `justif_field_bw5000_d3_h20_r30_dps80`
- Field `max_radicand` sensitivity:
  - `justif_field_r20_d3_h20_bw2000_dps80`
  - `justif_field_r30_d3_h20_bw2000_dps80`
  - `justif_field_r40_d3_h20_bw2000_dps80`
- Field `dps` sensitivity:
  - `justif_field_dps60_d3_h20_r30_bw2000`
  - `justif_field_dps80_d3_h20_r30_bw2000`
  - `justif_field_dps120_d3_h20_r30_bw2000`
- Beam `max_nodes` sensitivity:
  - `justif_beam_nodes15_d3_bw2000_dps80`
  - `justif_beam_nodes25_d3_bw2000_dps80`
  - `justif_beam_nodes35_d3_bw2000_dps80`

Use these to argue:
- `beam_width=2000` is a middle point after visible gains from 1000 and diminishing returns vs 5000.
- `max_radicand=30` is a practical tradeoff if gains from 30→40 are small.
- `dps=80` is ranking-stable versus 120 while cheaper than high-precision runs.
- beam `max_nodes=15` is a strict baseline; higher values show the sensitivity envelope.
