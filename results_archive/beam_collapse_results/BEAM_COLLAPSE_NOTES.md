### Beam search depth plateau – working notes

**Context**
- System: AEAS (Automated Euclidean Approximation System), `beam_search()` in `src/aeas/search.py`.
- Target: `cos(2π/n)`; focus so far on `n = 7, 11, 13` with `max_depth = 3` baseline, then deeper (`max_depth ≥ 4`).
- Observed behaviour: best error vs “sqrt-depth ≤ d” improves sharply up to depth 2–3, then **plateaus**; for `n = 13` depth 2 and 3 share the same best expression and error (~3.25e−8).

**Key observation about the plateau**
- Results at depth `d` store **the best expression among all sqrt-depths ≤ d**, not only exact depth `d`.
- In the baseline (`max_depth=3, max_nodes=15, beam_width=2000`):
  - `n=13, depth 2`: best_error ≈ 3.25e−8.
  - `n=13, depth 3`: identical expression and error.
- Interpretation: depth‑3 expressions are generated but **none beat the best depth‑2 candidate**, so the “best so far” curve flattens.
- This makes the search look like it “converges after third sqrt depth”, but that’s a **selection artefact**, not proof that deeper radicals can’t help.

**Why this is not a hard mathematical saturation**
- Grammar: rationals + `+, −, ×, ÷, √` under bounded depth/nodes.
- Over ℚ with nested square roots, the generated numbers form a dense subset of ℝ (within any finite interval), so there is no known theorem saying “no better than ~1e−8 for `cos(2π/13)` past sqrt-depth 3” under this grammar.
- Therefore, the persistent plateau is **overwhelmingly likely to be a search / pruning artefact**, not a limit of the representation.

**Search mechanics that bias against deep expressions**
1. **Error‑only competition with shallow expressions**
   - Sort key: `_sort_key = (error, node_count, to_str())`.
   - Deep expressions start life with relatively large error; shallow rationals often approximate the target surprisingly well early on.
   - During pruning, deep candidates are discarded before they can participate in enough compositions to become competitive.

2. **Depth‑wise diversity reservation shrinks as more levels are populated**
   - In `prune_diverse()`:
     - Group pool entries by `expr.sqrt_depth`.
     - Compute:
       - `n_levels = max(len(by_sd), 1)`
       - `reserved = max(beam_width // (3 * n_levels), 50)`
   - As search explores more sqrt-depth levels, `n_levels` increases and **reserved slots per level decrease**, exactly when deeper levels need more protection (their search space is exploding).

3. **Hard caps on deep expansions**
   - Current caps (pre‑change):
     - Phase 2 (sqrt × seeds): cap 500.
     - Phase 3 (sqrt × sqrt): cap **80**.
     - Phase 4 (compound(depth) × seeds): cap 200.
     - General cross-product: cap **100** (`top_n = min(100, len(pool_exprs))`).
     - Sqrt‑containing expressions participating in cross-product: cap **80**.
   - At higher sqrt-depths, the most promising structures are exactly **deep compositions of many sqrt nodes**, but only a tiny fixed subset (80/100) ever gets to interact in cross‑products.

4. **Too few general expansion rounds at high depth**
   - Current schedule:
     - `n_rounds = 3` for `depth == 0`.
     - `n_rounds = 2` for `depth > 0`.
   - This is inverted compared to what deep search needs: deeper levels have much richer combinatorics and require **more**, not fewer, rounds of (pool × seeds) and cross‑products to “catch up” with shallow approximations.

5. **Compound‑at‑depth expressions rarely combine with each other**
   - Phase 4 currently does `compound(depth) × seeds` only.
   - Expressions like `(sqrt(a)+b) * (sqrt(c)+d)` are only formed through the general cross-product, where they must compete directly with all depths by absolute error.
   - This further weakens the exploratory power at higher sqrt-depths.

**Planned / agreed mitigation strategies**
1. **Depth‑adaptive expansion caps**
   - Let caps for sqrt × sqrt and cross‑products **grow with depth** instead of staying fixed at 80/100.
   - Example plan:
     - `sqrt_sqrt_cap = min(80 * (1 + depth), len(new_sqrts), beam_width)`
     - `cross_top_n = min(100 + 50 * depth, len(pool_exprs), beam_width)`
     - `sqrt_pool_cap = min(80 * (1 + depth), beam_width)`

2. **Stronger per‑depth diversity retention**
   - Replace `reserved = beam_width // (3 * n_levels)` with a **per‑depth budget** that does not shrink as more levels are populated, e.g.:
     - `reserved_per_level = max(beam_width // (max_depth + 1), 50)`
   - Guarantees each sqrt-depth level keeps at least a fixed share of the beam, approximating a “partitioned beam”.

3. **More general expansion rounds at higher depth**
   - Depth‑adaptive round count, e.g.:
     - `n_rounds = 3` for `depth == 0`.
     - `n_rounds = max(3, 2 + depth // 2)` for `depth > 0`.
   - Gives deeper levels more composition cycles before pruning.

4. **Compound‑at‑depth cross‑product**
   - After Phase 4’s `compound(depth) × seeds`, also run `compound(depth) × compound(depth)` on the top current‑depth expressions.
   - Specifically target expressions like `(sqrt(a)+b) * (sqrt(c)+d)` that are difficult to reach otherwise.

5. **Slightly richer default constant set**
   - Add a small number of additional “nice” rationals (e.g. `2/3, 3/4, 4/3, 5/4`) to `DEFAULT_CONST_SET`.
   - These occur frequently in good trigonometric approximations and give the search more rational building blocks without exploding the initial pool.

**Stopping criteria thoughts (for later experiments)**
- Practical stop conditions for deeper search on fixed `n`:
  - **Error plateau**: increasing `max_depth` or `beam_width` improves best error by less than a chosen factor (e.g. < 2× improvement) over one or two steps.
  - **Visual tolerance for n‑gon rendering**: choose an error threshold on `cos(2π/n)` such that the resulting vertex positions differ by **less than one pixel** at the maximum intended screen radius; once achieved, deeper search is unnecessary for that target resolution.
- For future reporting, we should track both:
  - Best error at **exact** sqrt-depth `d` (to measure the benefit of deeper radicals).
  - Best error for `sqrt_depth ≤ d` (the plateau curve the CLI already shows).

