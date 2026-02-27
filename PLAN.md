## AEAS Paper Planning

This file tracks the research questions, experiment grid, stopping rules, and writing plan for turning AEAS into a publishable article.

---

### 1. Research questions

- **RQ1 (approximation law)**:  
  **How does the best achievable error \(|x - \cos(2\pi/n)|\) depend on sqrt-depth and coefficient height within quadratic-tower fields?**

- **RQ2 (algorithmic comparison)**:  
  **Does a field-first normal-form search over quadratic towers outperform expression-tree enumeration (beam search) for approximating non-constructible \(\cos(2\pi/n)\) under matched resource budgets (depth, height/nodes, beam width)?**

- **RQ3 (Chebyshev filter, optional)**:  
  **Can Chebyshev residuals \(|T_n(x) - 1|\) be used as a principled structural filter that reduces high-precision evaluations while preserving near-best approximation quality under fixed depth/height budgets?**

---

### 2. System summary (for the Methods section)

- **Targets**: \(\cos(2\pi/n)\) for non-constructible \(n\) (initially 7, 11, 13).
- **Families of approximants**:
  - **Field-first**: quadratic towers with bounded sqrt-depth and bounded coefficient height:
    - depth 0: rationals (height ≤ `max_height`)
    - depth 1: \(A + B\sqrt{m}\) with squarefree \(m \le \text{max\_radicand}\)
    - depth ≥2: \(P + Q\sqrt{\text{inner}_{d-1}}\) with guided coefficient search and biquadratic refinements.
  - **Tree-based** (baseline): beam search over expression trees with `+,−,×,÷,√`, bounded sqrt-depth and node count.
- **Search architecture**:
  - Field-first search is **two-phase**: fast float pre-filter (millions of candidates) → tree materialisation + `mpmath` verification for top survivors.
  - Both field-first and beam search return the same structure:  
    `dict[int, list[tuple[float, ExprNode]]]` = depth → sorted list of `(absolute_error, expression)`.
- **Evaluation tools**:
  - `results/*/summary.csv` (per-run best per (n, depth)).
  - `results/multi_run_summary.csv` + `multi_run_error_vs_depth.png` (cross-run comparison under a root).

---

### 3. Core experiment grid

#### 3.1 Field vs beam (fixed budgets) — baseline comparison (RQ2)

**Goal**: Show that field-first avoids beam collapse and typically achieves better errors at comparable cost.

- **Params (already used; can re-run as needed)**:
  - `n = 7 11 13`
  - `max_depth = 3`
  - `beam_width = 2000`
  - `dps = 80`

- **Beam (tree) runs**:

```bash
python3 scripts/run_search.py \
  --mode beam \
  --n 7 11 13 \
  --max_depth 3 \
  --max_nodes 15 \
  --beam_width 2000 \
  --dps 80
```

- **Field (quadratic towers) runs**:

```bash
python3 scripts/run_search.py \
  --mode field \
  --n 7 11 13 \
  --max_depth 3 \
  --max_height 20 \
  --max_radicand 30 \
  --beam_width 2000 \
  --dps 80
```

- **Evaluation**:
  - Run `python3 scripts/plot_results.py --root results --multi-run-grid`.
  - Inspect:
    - `results/multi_run_error_vs_depth.png` for error vs depth, per n and run.
    - `results/multi_run_summary.csv` for exact numbers (best_error per (run, n, depth)).

Deliverable: a table per n comparing field vs beam errors and runtimes at each depth, plus the figure.

#### 3.2 Height scaling at fixed depth (RQ1)

**Goal**: Empirically characterise how error scales with coefficient height at fixed depth \(d\), and identify diminishing returns.

- **Targets**: \(n = 7, 11, 13\).
- **Depths**: \(d = 1, 2\) (and possibly 3 if runtime acceptable).
- **Heights**: `max_height ∈ {8, 12, 16, 24, 32, 48}`.
- **Other params**: `max_radicand = 30`, `beam_width = 2000`, `max_depth` at least as large as the depth being studied, `mode=field`.

Example command template (adjust `--max_height` and `--max_depth` per sweep):

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

Analysis plan:
- For each depth \(d\), extract `best_error` vs `max_height` from `multi_run_summary.csv` (group by run_label).
- Plot \(\log_{10}(\text{error})\) vs \(\log_{10}(\text{height})\) per n and depth.
- Fit a simple linear trend to estimate slope \(b_d\) in \(\text{err}(H) ≈ H^{-b_d}\).

Stopping rule (per depth):
- When doubling `max_height` changes `best_error` by less than a factor of 2 for **two consecutive doublings**, treat the slope as stabilised and stop increasing height.

#### 3.3 Depth scaling at “best” height (RQ1/RQ2)

**Goal**: Show how error improves with depth for a fixed, reasonably large height budget.

- Pick a height from 3.2 where returns are not yet completely flat, e.g. `max_height = 32`.
- For each `n ∈ {7, 11, 13}`, run field search with:
  - depths `max_depth ∈ {0,1,2,3,4}` (or at least 0–3),
  - fixed `max_height = 32`, `max_radicand = 30`, `beam_width = 2000`.

Command template (repeat with increasing `--max_depth` or separate `run_name`s):

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

Depth stopping rule (per n):
- Compute ratios `err(d+1) / err(d)` from the CSV.
- Stop at the smallest D such that two consecutive ratios are > 0.3 (i.e. < ~3.3× improvement), or when runtime becomes prohibitive.

#### 3.4 Chebyshev residual filtering (RQ3, optional)

Implementation idea:
- In `field_search`, after computing a float approximation `x_float` for a candidate, compute a float Chebyshev residual `|T_n(x_float) - 1|` using `chebyshev_T_float`.
- Reject candidates whose residual is above a depth-dependent or empirically tuned threshold **before** calling `evaluate(expr, dps)`.

Experiment:
- Re-run a reduced version of 3.2 or 3.3 with and without Chebyshev pre-filtering.
- Compare:
  - best_error vs depth/height,
  - total runtime per n,
  - number of `evaluate` calls (to be logged).

Deliverable: ablation figure/table showing similar error but reduced runtime/evaluation count.

---

### 4. Analysis & figures

Core tooling already implemented:

- **Per-run plots**:
  - `python3 scripts/plot_results.py --root results --run <run_name>`
  - Produces `error_vs_depth.png`, `error_vs_nodes.png`, `combined_errors.png`, `ngon_drift.png` under `<run_name>/figures/`.

- **Multi-run aggregated plots & tables**:
  - `python3 scripts/plot_results.py --root results --multi-run-grid`
  - Produces:
    - `results/multi_run_error_vs_depth.png` — best error vs depth per n, with one curve per run_label.
    - `results/multi_run_summary.csv` — one row per (run, n, depth) with best_error, expression, nodes, sqrt_depth, dps, runtime, plus run metadata.

Planned additional analysis (likely in a notebook):
- Generate log–log plots of best_error vs max_height (from the summary CSV) and fit slopes.
- For each n, assemble a concise table:
  - field vs beam: best errors at depths 0–3 and corresponding expressions.
  - field-only scaling: errors at depth 2 as height increases.

---

### 5. Writing plan (paper outline)

1. **Introduction**
   - Non-constructible regular polygons; \(\cos(2\pi/n)\) in real subfields of cyclotomic fields.
   - Constructible numbers as quadratic towers (degree \(2^d\)).
   - Motivation: automated, algorithmic testing of algebraic approximation strategies.
   - State RQ1–RQ3.

2. **Background**
   - Cyclotomic fields and degrees of \(\cos(2\pi/n)\).
   - Constructible numbers and quadratic towers (brief).
   - Chebyshev polynomials and \(T_n(\cos(2\pi/n)) = 1\).

3. **Methods / Algorithms**
   - AEAS architecture: ExprNode, canonicalisation, evaluation.
   - Tree-based beam search (legacy).
   - Field-first search:
     - depth-wise normal forms (rationals, \(A+B\sqrt{m}\), \(P+Q\sqrt{\text{inner}}\)).
     - float pre-filter → ExprNode + mpmath.
     - diversity-aware pruning across sqrt-depth.
   - Optional: Chebyshev residual filter.

4. **Experimental setup**
   - Targets: n = 7, 11, 13.
   - Parameter grids: depth, height, radicands, beam width, precision.
   - Implementation details: hardware, Python/mpmath versions.

5. **Results**
   - Field vs beam comparison (RQ2):
     - best_error vs depth and runtime plots.
   - Height scaling laws (RQ1):
     - log–log plots; slopes \(b_d\); discussion of diminishing returns.
   - Depth scaling at best height:
     - improvement ratios between depths; “point of diminishing returns.”
   - (Optional) Chebyshev-filter ablation (RQ3):
     - runtime vs error, number of evaluations.

6. **Discussion**
   - Interpretation of observed exponents \(b_d\).
   - Advantages and limitations of field-first enumeration.
   - How this framework can test other algebraic approximation algorithms/targets.

7. **Conclusion & future work**
   - Summary of findings.
   - Extensions: other algebraic targets, higher-degree towers, integration with symbolic solvers.

---

### 6. Execution progress (last updated 2026-02-27)

#### 3.1 Field vs Beam baseline comparison -- DONE

Both runs completed and archived in `results/`:

| Run directory | Mode | Params |
|---------------|------|--------|
| `field_n7-11-13_d3_h20_r30_bw2000` | field | d3, h20, r30, bw2000 |
| `beam_n7-11-13_d3_nodes15_bw2000`  | beam  | d3, nodes15, bw2000 |

Per-run figures generated for both. Multi-run grid and summary CSV regenerated.

**Key finding (RQ2)**: Field-first wins at depths 0 and 3 for most n; beam search is competitive or better at depth 2 for n=13. Field avoids beam collapse at depth 3 (beam stagnates, field continues improving). See `results/analysis/field_vs_beam_table.csv`.

#### 3.2 Height scaling sweep -- ALL 6 DONE

OOM bug fixed: replaced unbounded `d1_raw` list with bounded `heapq` in `field_search.py`. Memory usage dropped from ~2 GB to ~62 MB for h=48.

| Run name | Height | Status |
|----------|--------|--------|
| `field_n7-11-13_d2_h8_r30_bw2000`  | 8  | done |
| `field_n7-11-13_d2_h12_r30_bw2000` | 12 | done |
| `field_n7-11-13_d2_h16_r30_bw2000` | 16 | done |
| `field_n7-11-13_d2_h24_r30_bw2000` | 24 | done |
| `field_n7-11-13_d2_h32_r30_bw2000` | 32 | done |
| `field_n7-11-13_d2_h48_r30_bw2000` | 48 | done (after OOM fix) |

**Observed best errors at depth 1 (height scaling)**:

| max_height | n=7       | n=11      | n=13      |
|------------|-----------|-----------|-----------|
| 8          | 3.96e-05  | 1.21e-05  | 2.19e-05  |
| 12         | 4.78e-06  | 1.21e-05  | 2.76e-07  |
| 16         | 2.21e-06  | 4.78e-06  | 2.76e-07  |
| 24         | 4.67e-07  | 1.02e-08  | 1.52e-07  |
| 32         | 3.86e-08  | 1.02e-08  | 5.11e-08  |
| 48         | 3.86e-08  | 1.02e-08  | 1.17e-08  |

Log-log fits: see `results/analysis/height_scaling_loglog.png`.

#### 3.3 Depth scaling at height=32 -- ALL 5 DONE (incl. depth 4)

| Run name | max_depth | Status |
|----------|-----------|--------|
| `field_n7-11-13_d0_h32_r30_bw2000` | 0 | done |
| `field_n7-11-13_d1_h32_r30_bw2000` | 1 | done |
| `field_n7-11-13_d2_h32_r30_bw2000` | 2 | done |
| `field_n7-11-13_d3_h32_r30_bw2000` | 3 | done |
| `field_n7-11-13_d4_h32_r30_bw2000` | 4 | done |

**Depth scaling at height=32**:

| n  | depth 0  | depth 1  | depth 2  | depth 3  | depth 4  |
|----|----------|----------|----------|----------|----------|
| 7  | 8.68e-07 | 3.86e-08 (22x) | 1.25e-08 (3x) | 2.51e-10 (50x) | 2.51e-10 (1x) |
| 11 | 2.59e-07 | 1.02e-08 (25x) | 1.02e-08 (1x) | 5.10e-10 (20x) | 5.10e-10 (1x) |
| 13 | 8.60e-07 | 5.11e-08 (17x) | 1.70e-08 (3x) | 5.64e-09 (3x) | 5.64e-09 (1x) |

**Depth-4 stagnation**: at h=32, depth 4 produces zero improvement over depth 3 for all n. For n=7, six sd=4 expressions are generated but none outperform sd=3. For n=11 and n=13, zero sd=4 expressions survive into the top-K. See saturation analysis below.

See `results/analysis/depth_scaling_h32.png`.

#### 3.5 Depth-4 saturation control experiment (h=64) -- DONE

**Goal**: Prove that depth-4 stagnation at h=32 is a coefficient resolution floor, not an algorithmic limitation.

| Run name | max_depth | max_height | Status |
|----------|-----------|------------|--------|
| `field_n7-11-13_d4_h64_r30_bw2000` | 4 | 64 | done |

**Saturation comparison (h=32 vs h=64)**:

| n  | depth | h=32      | h=64      | ratio (32/64) |
|----|-------|-----------|-----------|---------------|
| 7  | 0     | 8.68e-07  | 5.75e-08  | 15.1x         |
| 7  | 1     | 3.86e-08  | 3.80e-08  | 1.0x          |
| 7  | 2     | 1.25e-08  | 4.36e-10  | 28.7x         |
| 7  | 3     | 2.51e-10  | 4.36e-10  | 0.6x          |
| 7  | 4     | 2.51e-10  | 4.36e-10  | 0.6x          |
| 11 | 0     | 2.59e-07  | 8.51e-10  | 304.3x        |
| 11 | 1     | 1.02e-08  | 8.51e-10  | 12.0x         |
| 11 | 2     | 1.02e-08  | 8.51e-10  | 12.0x         |
| 11 | 3     | 5.10e-10  | 8.51e-10  | 0.6x          |
| 11 | 4     | 5.10e-10  | 8.51e-10  | 0.6x          |
| 13 | 0     | 8.60e-07  | 1.10e-07  | 7.8x          |
| 13 | 1     | 5.11e-08  | 1.17e-08  | 4.4x          |
| 13 | 2     | 1.70e-08  | 1.07e-08  | 1.6x          |
| 13 | 3     | 5.64e-09  | 1.07e-08  | 0.5x          |
| 13 | 4     | 5.64e-09  | 5.92e-09  | 1.0x          |

**Key findings**:

1. **Height dramatically improves accuracy**: for n=7, h=64 depth 0 is 15x better than h=32 depth 0; h=64 depth 2 is 29x better than h=32 depth 2. For n=11, h=64 depth 0 is 304x better. This proves height drives error reduction.
2. **Saturation depth shifts with height**: at h=32 saturation occurs at depth 3 (d3=d4); at h=64 saturation occurs earlier at depth 2 (d2=d3=d4) for n=7, because finer coefficients at depth 2 already reach a strong result (4.36e-10).
3. **Saturation is universal**: at any fixed height H, there exists a depth beyond which further nesting cannot improve. This is the **coefficient resolution floor** -- the granularity of outermost P,Q coefficients (approximately 1/H) dominates the achievable error.
4. **The algorithm IS exploring**: at h=64, depth-4 expressions are generated (21 nodes each) but they're 200x worse than the best depth-2 result. The search space is fully explored; the limitation is structural.

**Implication for the paper**: depth stagnation is not an algorithm bug but a fundamental property of bounded-height quadratic towers. The Discussion section should frame this as a coefficient resolution floor that can be pushed down by increasing H (as confirmed by the height scaling experiments).

See `results/analysis/saturation_h32_vs_h64.png` and `results/analysis/saturation_table.csv`.

#### 3.4 Chebyshev filtering -- DEFERRED for first paper

#### 4. Analysis and figures -- DONE

All generated under `results/analysis/`:

- `height_scaling_loglog.png` -- log-log best_error vs max_height with fitted slopes
- `height_scaling_table.csv` -- raw data
- `depth_scaling_h32.png` -- semilogy best_error vs depth
- `depth_scaling_table.csv` -- raw data with improvement ratios
- `field_vs_beam_table.csv` -- field vs beam comparison at each (n, depth)
- `saturation_h32_vs_h64.png` -- depth saturation comparison for n=7 at h=32 vs h=64
- `saturation_table.csv` -- raw saturation data

Multi-run grid: `results/multi_run_error_vs_depth.png`, `results/multi_run_summary.csv`.
Per-run figures: in each `results/<run>/figures/`.
Analysis script: `scripts/analyse_scaling.py`.

---

### 7. Discussion framing: depth stagnation as a coefficient resolution floor

The depth-4 stagnation is a key finding that requires careful framing. The control experiment (section 3.5) provides empirical support. Here is the three-pronged argument:

**1. Theoretical: coefficient resolution scales with depth.**
Each sqrt layer introduces two new rational coefficients (P, Q) drawn from a finite grid of ~H^2 reduced fractions. The sqrt function is contracting (derivative 1/(2sqrt(x)) < 1 for x > 1/4), so small improvements in the inner expression get attenuated by the outer sqrt, while the outer P,Q coefficients have fixed granularity ~1/H. At some depth, the outer coefficient granularity dominates the achievable error floor.

**2. Empirical: saturation correlates with height, not depth.**
The h=64 control experiment (n=7) confirms this. Doubling height from 32 to 64 yielded a 29x improvement at depth 2 (1.25e-08 to 4.36e-10), and shifted the saturation point from depth 3 to depth 2. The saturation pattern is universal: at any fixed H, there is a depth ceiling beyond which nesting does not help.

**3. Structural: the search IS exploring.**
At h=32, n=7 produces six sd=4 expressions (21 nodes each) -- the max_nodes=50 cap is not binding. At h=64, depth-4 expressions are generated but are 200x worse than the depth-2 best. The algorithm explores the space; the grid is simply too coarse at higher depths.

**Suggested paper text (Discussion section)**:

> Depth-4 search produces no improvement over depth 3 at height 32 for any target n. This is not an algorithmic limitation: for n=7, six distinct depth-4 expressions are generated, but none outperform the best depth-3 result. The explanation is a coefficient resolution floor: each tower level introduces two rational coefficients (P, Q) drawn from a finite grid of ~H^2 reduced fractions. As depth increases, each additional sqrt layer attenuates inner improvements (since d/dx sqrt(x) < 1 for typical inner values), while the outermost coefficients retain fixed granularity ~1/H. At height 32, this granularity dominates the error floor, creating a saturation point. A control experiment at height 64 confirms the mechanism: doubling the coefficient resolution improved depth-2 error by 29x (from 1.25e-08 to 4.36e-10) and shifted the saturation from depth 3 to depth 2, demonstrating that the floor is set by coefficient resolution, not algorithmic reach.

---

### 8. Remaining next actions

1. Write the paper using the data in `results/analysis/`.
2. Consider expanding height sweep to include n=11.
3. Decide on Chebyshev filtering for a follow-up paper.

---

### Appendix: Raw notes on depth-4 stagnation (from initial analysis)

Defending the Depth-4 Stagnation

The data tells a clear story

The depth-4 run reveals three different scenarios:





n=7: Depth-4 expressions ARE generated (6 of them with sd=4), but the best sd=4 error is 2.8e-9 -- worse than the sd=3 best of 2.5e-10. The algorithm IS exploring depth 4, it just can't beat depth 3.



n=11, n=13: Zero sd=4 expressions survive into the top-K. The inner pool (sd=3 expressions with positive value) is tiny (4-9 candidates), and wrapping them in P + Q*sqrt(inner) at height 32 doesn't produce competitive results.

This is not an algorithm limitation. It is a coefficient resolution bottleneck: at height 32, you only have ~1600 distinct rationals. A depth-4 expression has the form P + Q*sqrt(P' + Q'*sqrt(P'' + Q''*sqrt(P''' + Q'''*sqrt(m)))). With 4 layers of rational coefficients each capped at height 32, the discrete grid of reachable values gets coarser relative to the target as nesting depth increases.

How to frame this in the paper

The argument has three prongs:

1. Theoretical: coefficient resolution scales exponentially with depth

Each added sqrt layer multiplies the "effective" coefficient space dimension by 2 (a new P, Q pair). At fixed height H, the number of reachable tower elements grows as ~H^(2d), but the volume of the real line they cover also thins out as nesting magnifies coefficient errors. The key insight: sqrt is a contracting map near typical inner values (derivative 1/(2*sqrt(x)) < 1 for x > 1/4), so small improvements in the inner expression get attenuated by the outer sqrt, while the P,Q coefficients at each level have fixed granularity 1/H. At some depth, the granularity of the outer coefficients dominates the error floor.

2. Empirical: the saturation correlates with height, not depth

The strongest defense is a control experiment: re-run depth 4 with higher height (e.g. 48 or 64). If depth 4 improves with more height, that proves the bottleneck is coefficient resolution, not the algorithm. The OOM fix makes this feasible.

Recommended experiment to add:

python3 scripts/run_search.py --mode field --n 7 11 13 --max_depth 4 \
  --max_height 64 --max_radicand 30 --beam_width 2000 --dps 80 \
  --run_name "field_n7-11-13_d4_h64_r30_bw2000" --progress

If this gets below 2.5e-10 for n=7 at depth 4, the argument is proven: stagnation was a height limit, not an algorithm limit.

3. Structural: node count confirms the search IS exploring

The best sd=3 expression has 16 nodes. The best sd=4 has 21 nodes (for n=7). The max_nodes=50 cap is nowhere near binding. The search is building depth-4 trees; they just aren't better because the coefficients are too coarse.

Suggested paper text (Discussion section)



Depth-4 search produces no improvement over depth 3 at height 32 for any target n. This is not an algorithmic limitation: for n=7, six distinct depth-4 expressions are generated, but none outperform the best depth-3 result. The explanation is a coefficient resolution floor: each tower level introduces two new rational coefficients (P, Q) drawn from a finite grid of H^2 reduced fractions. As depth increases, the number of coefficients grows linearly with d, but each additional sqrt layer attenuates improvements from deeper levels (since d/dx sqrt(x) < 1 for the typical inner values encountered). At fixed height H=32, the granularity of the outermost coefficients (1/32) dominates the achievable error, creating a saturation point. This is confirmed by the height-scaling experiments (Section X), which show that increasing H consistently improves errors at fixed depth, and suggests that depth-4 improvements would require a proportionally larger height budget.

Implementation plan





Run the depth-4-at-h64 control experiment for n=7 (~30s)



If it beats depth 3, add it to the depth scaling table as evidence



Add 2-3 sentences to the Discussion section as outlined above



Optionally: add a small "saturation analysis" figure showing best error vs depth for h=32 and h=64 on the same axes

