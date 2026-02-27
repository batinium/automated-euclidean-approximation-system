# Results Pickup Notes (Post-Rerun)

This note summarizes what changed after patching analysis and rerunning outputs.

## 1) Which field-vs-beam table to cite

Use these files under `results/analysis/`:

- `field_vs_beam_baseline_table.csv`
  - Strict canonical baseline pair only:
    - beam: `beam_n7-11-13_d3_nodes15_bw2000`
    - field: `field_n7-11-13_d3_h20_r30_bw2000`
  - Use this for the main RQ2 baseline claim.

- `field_vs_beam_bestof_table.csv`
  - Best-by-mode across all available runs (includes extra experiments).
  - Use this as an auxiliary robustness/capacity context table.

- `field_vs_beam_table.csv`
  - Backward-compatible alias of `field_vs_beam_baseline_table.csv`.

## 2) Parameter-justification outcomes (from new runs)

### Field beam width (`bw=1000,2000,5000`; d3,h20,r30,dps80)
- Depth-3 best errors are identical for all n in this sweep.
- Runtime increases with width:
  - 1000 -> 2000: ~1.13x
  - 2000 -> 5000: ~1.46x
- Interpretation: `beam_width=2000` is a good operating point.

### Field radicand bound (`r=20,30,40`; d3,h20,bw2000,dps80)
- Depth-3 error improves from r20 to r40 for n=7 and n=11 (~1.9-2.0x), unchanged for n=13.
- Runtime overhead in these runs is small.
- Interpretation: `max_radicand=30` is a practical compromise; r40 can be justified for quality-focused sweeps.

### Field precision (`dps=60,80,120`; d3,h20,r30,bw2000)
- Depth-3 best errors are identical in this sweep.
- Interpretation: `dps=80` is ranking-stable and reasonable as default.

### Beam node budget (`max_nodes=15,25,35`; d3,bw2000,dps80)
- Depth-3 best error improves strongly from 15 -> 35:
  - n=7: ~124.7x
  - n=11: ~115.4x
  - n=13: ~213.0x
- Runtime rises ~3.23x on average.
- Interpretation: beam baseline quality is highly node-budget sensitive.

## 3) Files regenerated and ready

- `results/analysis/height_scaling_table.csv`
- `results/analysis/depth_scaling_table.csv`
- `results/analysis/saturation_table.csv`
- `results/analysis/field_vs_beam_baseline_table.csv`
- `results/analysis/field_vs_beam_bestof_table.csv`
- all analysis PNGs under `results/analysis/`

## 4) Suggested report usage

- Main comparison table in paper: baseline CSV.
- Add one short paragraph with best-of table as robustness context.
- Add one methods paragraph citing the parameter-justification sweeps for `beam_width`, `max_radicand`, and `dps` defaults.
