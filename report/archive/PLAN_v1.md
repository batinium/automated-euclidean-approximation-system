# AEAS Report Plan (Single Source of Truth)

This file is the canonical handoff/planning document for the paper.
It replaces previous split notes (`PATCHLIST.md`, `RESULTS_PICKUP.md`).

## 1) Current status

Completed:
- Full reruns completed (core + extras + justification sweeps).
- Analysis regenerated and aligned with manuscript.
- CS-oriented manuscript is now the canonical and only maintained report source (`report/aeas_paper.tex`).
- Field-vs-beam reporting split into:
  - baseline-only table
  - best-of-by-mode table
- Manuscript (`report/aeas_paper.tex`) updated with:
  - softened fairness wording
  - baseline vs best-of distinction
  - denominator-cap caveat (`q_height <= 14`)
  - pooled-minima caveat
  - limitations subsection

Pending before final submission:
- Fill author names.
- Add bibliography/citations.
- Add beam-collapse diagnostic figure/table.
- Add environment/runtime provenance table in paper body.
- Optional but recommended: ablate/remove denominator cap and rerun saturation-focused claims.

## 2) Canonical artifacts to cite

Primary analysis outputs (under `results/analysis/`):
- `field_vs_beam_baseline_table.csv` (main RQ2 baseline table)
- `field_vs_beam_bestof_table.csv` (robustness context)
- `height_scaling_table.csv`
- `depth_scaling_table.csv`
- `saturation_table.csv`

Main figures (same folder):
- `height_scaling_loglog.png`
- `depth_scaling_h32.png`
- `saturation_h32_vs_h64.png`
- `search_architecture.png`
- `expr_tree_n7_d3_r1.png`, `expr_tree_n11_d3_r1.png`, `expr_tree_n13_d3_r1.png`
- `depth1_heatmap_n7_m2_h32.png`, `depth1_heatmap_n11_m2_h32.png`
- `tower_layers_n7.png`, `tower_layers_n11.png`, `tower_layers_n13.png`

## 3) Parameter-default justification (already run)

Field beam width (`bw=1000,2000,5000`; d3,h20,r30,dps80):
- Depth-3 best errors unchanged across tested widths.
- Runtime: ~1.13x (1000->2000), ~1.46x (2000->5000).
- Interpretation: `beam_width=2000` is a practical operating point.

Field radicand bound (`r=20,30,40`; d3,h20,bw2000,dps80):
- Improvement at depth 3 for n=7 and n=11 from r20->r40; n=13 unchanged.
- Runtime overhead modest in current runs.
- Interpretation: `max_radicand=30` is a balanced default.

Field precision (`dps=60,80,120`; d3,h20,r30,bw2000):
- Depth-3 best errors unchanged.
- Interpretation: `dps=80` is stable and efficient.

Beam node budget (`max_nodes=15,25,35`; d3,bw2000,dps80):
- Large quality gains at 35 vs 15, with substantial runtime increase.
- Interpretation: beam baseline is strongly node-budget sensitive.

## 4) Report-writing guidance

When writing results:
- Use baseline table for main method-comparison claim.
- Use best-of table only as robustness/capacity context.
- Keep claims scoped to configuration.
- Mention depth-scaling values are pooled minima (lower envelopes).
- Mention denominator-cap caveat for depth>=2 coefficients.

## 5) Operational commands

Rerun everything sequentially:
- `bash scripts/rerun_all.sh --purge-results`

Include extra robustness runs:
- `bash scripts/rerun_all.sh --purge-results --extra-experiments`

Include parameter-justification suite:
- `bash scripts/rerun_all.sh --purge-results --justification-experiments`

Regenerate analysis only:
- `python3 scripts/analyse_scaling.py`

## 6) File map for handoff

- Manuscript: `report/aeas_paper.tex`
- This plan: `report/PLAN.md`
- Experiment runner: `scripts/rerun_all.sh`
- Execution playbook: `runs.md`
