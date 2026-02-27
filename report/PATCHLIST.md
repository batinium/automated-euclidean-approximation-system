# AEAS Paper Patch List (Critical + Detailed)

This patch list is prioritized for turning `report/aeas_paper.tex` into a defensible methods/results paper.

## P0 (must fix before submission)

### 1) Correct the fairness claim in field-vs-beam comparison
- Problem: the text repeatedly says "matched resource budgets," but implementation is not matched in effective capacity.
- Evidence:
  - Field mode forces `max_nodes >= 50`: `scripts/run_search.py:155`
  - Beam baseline run uses `max_nodes = 15` (`results/beam_n7-11-13_d3_nodes15_bw2000/run_config.json`)
- Paper locations to patch:
  - `report/aeas_paper.tex:23`
  - `report/aeas_paper.tex:51`
  - `report/aeas_paper.tex:158`
  - `report/aeas_paper.tex:177`
  - `report/aeas_paper.tex:182`
- Required change:
  - Replace "matched resource budgets" wording with either:
    - "comparable practical budgets (same beam width and max depth, different parameterizations)," or
    - run a truly matched experiment and update table accordingly.
- Suggested replacement sentence (Experimental setup paragraph):
  - "We compare field-first and beam search under comparable practical budgets (same max depth and beam width), noting that method-specific constraints differ (field search enforces a larger node budget and explicit coefficient-height limits)."

### 2) Disclose and handle the deep-level coefficient cap (`q_height <= 14`)
- Problem: depth `>=2` search caps denominator search by `q_height = min(max_height, 14)`, so `H=32/64` does not fully propagate to outer coefficients.
- Evidence: `src/aeas/field_search.py:373`
- Why it matters: this can induce apparent depth saturation and confound the "coefficient resolution floor" claim.
- Paper locations to patch:
  - `report/aeas_paper.tex:24`
  - `report/aeas_paper.tex:120-127` (nested depth description)
  - `report/aeas_paper.tex:282-287`
  - `report/aeas_paper.tex:356`
- Required change:
  - Add explicit implementation note in Methods:
    - "For depth >=2, denominator search is currently capped at 14 for compute control."
  - Reframe conclusions as provisional unless rerun with this cap removed/ablated.
- Minimum acceptable wording in Results/Discussion:
  - "Observed saturation may reflect both structural approximation limits and the current depth>=2 denominator cap in our implementation."

### 3) Clarify pooled-minimum aggregation in depth scaling
- Problem: depth table values are minima pooled across multiple runs (`max_depth >= d`), not one run trajectory.
- Evidence:
  - Paper already hints this in one table caption (`report/aeas_paper.tex:256`), but conclusions are phrased as if from single controlled sweep.
  - Aggregation logic: `scripts/analyse_scaling.py:262`
- Locations to patch:
  - `report/aeas_paper.tex:250-272`
  - `report/aeas_paper.tex:340-343`
- Required change:
  - Explicitly label curves/tables as "cross-run lower envelopes" where applicable.
  - Add one sentence that these pooled minima may overstate monotonic trends.
- Suggested addendum sentence:
  - "These depth curves are pooled minima across runs with different maximum depths and should be interpreted as lower envelopes rather than single-run trajectories."

## P1 (high value, likely reviewer comments)

### 4) Soften over-strong causal claims
- Problem: claims like "field-first outperforms" and "precisely explains" are stronger than current ablation/statistical support.
- Locations:
  - `report/aeas_paper.tex:208-210`
  - `report/aeas_paper.tex:345-348`
  - `report/aeas_paper.tex:356-357`
- Required change:
  - Use scoped language: "in this benchmark grid," "under current tuning," "suggests," "consistent with."
- Example replacement:
  - "In this benchmark grid, field-first is generally more robust at deeper levels, while beam search remains competitive in specific cases (notably n=13 at depth 2)."

### 5) Add explicit limitations subsection
- Insert new subsection before Conclusion.
- Include at least:
  - No uncertainty intervals (deterministic runs, no stochastic confidence estimates).
  - Method-capacity mismatch in field vs beam settings.
  - Depth>=2 denominator cap in nested search.
  - Pooled-minimum aggregation caveat.
- Suggested insertion point:
  - After `report/aeas_paper.tex:351`, before `\section{Conclusion and future work}`.

### 6) Add reproducibility metadata in paper body
- Problem: no environment/runtime provenance table in manuscript.
- Add short table with:
  - Python version, package versions (`mpmath`, `numpy`, `pandas`, `matplotlib`), CPU/RAM, OS, date of runs.
  - Exact run directories used for each figure/table.
- Suggested insertion:
  - End of Experimental setup section (`report/aeas_paper.tex` after line 171).

## P2 (paper polish + completeness)

### 7) Fill author and add references
- Problem: `\author{TODO: Author Name(s)}` still present.
- Location: `report/aeas_paper.tex:10`
- Add citations for:
  - Gauss-Wantzel theorem source(s)
  - Constructible number references
  - Cyclotomic/cosine degree background
- Also add short related work paragraph in Background.

### 8) Tighten claim around "beam collapse"
- Problem: qualitative phrasing is strong but collapse diagnostics are not shown in the paper.
- Add one compact diagnostic table/figure (e.g., unique-expression diversity by depth for beam vs field).
- Candidate source artifacts: `results_archive/beam_collapse_results/*` and notes file.

### 9) Distinguish algorithm diagrams from empirical figures
- Current Figure 1 architecture diagram is conceptual; make that explicit in caption:
  - "Schematic (not data-derived)."

## Codebase patch list (if you want paper claims to be stronger)

### C1) Remove or ablate denominator cap in nested search
- File: `src/aeas/field_search.py:373`
- Current:
  - `q_height = min(max_height, 14)`
- Options:
  - A) Use `q_height = max_height` and report runtime impact.
  - B) Keep cap but run ablation `{14, 24, 32, 64}` and show saturation sensitivity.

### C2) Collision-safe dedup in field search
- File: `src/aeas/field_search.py:147-163`
- Current dedup uses `seen: set[int]` with hashes only.
- Patch target:
  - Use `seen: set[ExprNode]` or a tuple key from canonical string + op structure.

### C3) Add analysis script guardrails
- File: `scripts/analyse_scaling.py`
- Add explicit label/column in CSV outputs indicating:
  - pooled-minimum vs single-run metric.
  - data provenance (run list used).

### C4) Add fairness runner script
- New script recommendation: `scripts/compare_fair.py`
- Should enforce either:
  - equal runtime budget per n, or
  - equal candidate materialisation budget, then compare best error.

## Concrete text edits (quick copy set)

### Abstract edits
- `report/aeas_paper.tex:23`
  - Replace with: "Compared to an expression-tree beam search baseline, the field-first search is generally more robust at higher depths in our benchmark grid under comparable practical budgets."
- `report/aeas_paper.tex:24`
  - Append caveat: "... although this saturation is also influenced by implementation-level coefficient-search limits at deeper levels."

### Experimental setup edits
- `report/aeas_paper.tex:158`
  - Replace "matched resource budgets" phrase with "comparable practical budgets" and mention differing constraints.

### Results/Discussion edits
- `report/aeas_paper.tex:208-210`
  - Rephrase from dominance claim to mixed-outcome claim.
- `report/aeas_paper.tex:282-287`
  - Add caveat about deep-level denominator cap.
- `report/aeas_paper.tex:356`
  - Replace "outperforms" with "often outperforms in this benchmark configuration".

## Regeneration checklist after edits

1. Regenerate tables/figures from current runs:
   - `python scripts/plot_results.py --root results --multi-run-grid`
   - `python scripts/analyse_scaling.py`
2. If C1 is applied, rerun depth/height sweeps and refresh:
   - `results/analysis/depth_scaling_table.csv`
   - `results/analysis/saturation_table.csv`
   - associated figures.
3. Recompile paper and verify all figure paths resolve from `report/`.

## Priority execution order

1. P0-1 fairness wording patch.
2. P0-2 denominator-cap disclosure (or rerun with cap change).
3. P0-3 pooled-minimum clarification.
4. P1 limitations subsection.
5. P2 metadata/references polish.

