# AEAS Publication Audit — Literature Gap & Q1 Readiness

**Date:** 2026-04-20
**Scope:** Assess whether current AEAS experiments support a Q1 journal/conference submission or remain an ablation-heavy systems note. Methodology: independent literature survey via Consensus (peer-reviewed database), plus an independent critical review delegated to `codex exec` over the manuscript, PLAN, analysis CSVs, and source tree.

---

## 1. Executive verdict

**The project as currently scoped does not clear a Q1 bar.** It is a competent, reproducible prototype with a plausible systems idea (field-first normal-form search with delayed symbolic materialization), but the empirical base is three hand-picked targets, the only baseline is an in-house beam, compute is not matched, the denominator cap at `q_height <= 14` is conflated with depth saturation, and there is no theorem, benchmark, or external baseline. The parameter sweeps are appendix material, not a main contribution.

**Closest plausible targets as-is (rough acceptance likelihood):**

| Venue | As-is | With the fixes in §5 |
|---|---|---|
| *Experimental Mathematics* (short note) | ~10–15% | ~40–55% |
| ISSAC software/workshop track | ~15–25% | ~45–60% |
| *Journal of Symbolic Computation* (JSC) | <10% | ~25–40% |
| ACM TOMS | <5% (no benchmark story) | ~15–25% |
| NeurIPS D&B / AAAI workshop (as benchmark) | <5% | ~30–45% |

---

## 2. Literature gap analysis

Four tracks matter for positioning AEAS. Codex audit plus Consensus search surface the following prior work. I flag each track's gap status and where AEAS's claimed contribution lands.

### 2.1 Explicit constructible approximations to non-constructible polygons

- Williamson, *Approximate construction of the regular heptagon*, Math. Gazette 1955; Goormaghtigh 1956; Perkins 2005; Spíchal 2026 (Math Horizons).
- Hogendijk, *Greek and Arabic constructions of the regular heptagon*, Arch. Hist. Exact Sci. 1984.
- Benjamin & Snyder, *On the construction of the regular hendecagon by marked ruler and compass*, Math. Proc. Camb. Phil. Soc. 2014.

**Gap:** Real. These are hand-designed recipes; none do systematic height-bounded search in explicit quadratic towers. But the gap is narrow — most readers in this community care about closed-form elegance, not algorithmic enumeration. Confidence: medium-high.

### 2.2 Nested radicals, denesting, normal forms for algebraic expressions

- Landau, *Simplification of nested radicals*, FOCS 1989 / SICOMP 1992 — foundational decision procedure, polynomial in size of splitting field. ([paper](https://consensus.app/papers/details/cac641b484d65cee899fb5a117e88a84/?utm_source=claude_desktop))
- Zippel, *Simplification of Expressions Involving Radicals*, J. Symb. Comput. 1985. ([paper](https://consensus.app/papers/details/8db54c29287354fe8ec46ca28cf43744/?utm_source=claude_desktop))
- Blömer, *How to Denest Ramanujan's Nested Radicals*, 1992. ([paper](https://consensus.app/papers/details/c1410bac1e55500ca272e16f2897e938/?utm_source=claude_desktop))
- Osipov et al., *Simplification of Nested Real Radicals Revisited*, 2021. ([paper](https://consensus.app/papers/details/43ae75d90d34567495b2744e8e1de7c7/?utm_source=claude_desktop))
- Landau, *How to tangle with a nested radical*, Math. Intelligencer 1991. ([paper](https://consensus.app/papers/details/818a035323355c4bb5faf4478e0f5314/?utm_source=claude_desktop))

**Gap:** Mixed. Denesting literature solves the inverse problem (simplify given radical). AEAS solves a forward problem (search for low-error radicals within a height-bounded tower). These are complementary but the reviewer pool will expect AEAS's canonicalization step to engage with Landau/Zippel/Blömer. Currently the manuscript does not cite any of them. Confidence: high.

### 2.3 Symbolic search / symbolic regression / deterministic enumeration

The field-first vs syntax-first distinction is anticipated and well-populated:

- **Directly analogous.** Kammerer et al., *Symbolic Regression by Exhaustive Search: Reducing the Search Space Using Syntactical Constraints and Efficient Semantic Structure Deduplication*, 2021. Deterministic enumeration + semantic dedup via caching — AEAS's canonicalization-before-insert is in the same family. ([paper](https://consensus.app/papers/details/1977fcb76e555597a3578c098ccb7aae/?utm_source=claude_desktop))
- Kahlmeyer et al., *Scaling Up Unbiased Search-based Symbolic Regression*, 2024. Small-expression systematic search outperforms SOTA on recovery. ([paper](https://consensus.app/papers/details/42a4ea5e1bb8546c8acacb02fdaa799e/?utm_source=claude_desktop))
- Anselment et al., *Systematic tree search for symbolic regression*, CEAS Aero J. 2025 (dimensional analysis + systematic spanning). ([paper](https://consensus.app/papers/details/5197064d27ab5d538108b55dbc0979de/?utm_source=claude_desktop))
- França, *A greedy search tree heuristic for symbolic regression (SymTree / IT)*, 2018 — IT-style constrained search space. ([paper](https://consensus.app/papers/details/a9253f5597b8535ea5dc51b37e630b77/?utm_source=claude_desktop))
- Udrescu & Tegmark, *AI Feynman*, Sci. Adv. 2020; Petersen et al., *Deep Symbolic Regression*, ICLR 2021; Biggio et al., *Neural Symbolic Regression that Scales*, ICML 2021; Kamienny et al., *Deep Generative SR with MCTS*, 2023; Shojaee et al., *TPSR*, 2023; La Cava et al., *Contemporary SR Methods and their Relative Performance*, NeurIPS D&B 2021; França et al., *SRBench++*, IEEE TEVC 2024.
- Koza 1992; Schmidt & Lipson, Science 2009; Moraglio/Krawiec/Johnson, *Geometric Semantic GP*, PPSN 2012.

**Gap:** The *general* claim "semantic/normal-form search beats syntax-first enumeration" is not new — Kammerer 2021 and Kahlmeyer 2024 make the closest claim. AEAS's narrower version ("delayed expression materialization over a *quadratic-tower* index over *algebraic numbers*") is more specific and plausibly novel, but it has to be argued against these papers explicitly. Confidence: high.

### 2.4 Diophantine approximation & algebraic-number theoretic baselines

- Roth, *Rational approximations to algebraic numbers*, Mathematika 1955.
- Davenport & Schmidt, *Approximation to real numbers by quadratic irrationals*, Acta Arith. 1967.
- Schmidt, *Simultaneous Approximation to Algebraic Numbers by Elements of a Number Field*, Monatsh. Math. 1975.
- Bugeaud, *Approximation by Algebraic Numbers*, Cambridge 2004.
- Schleischitz, *Diophantine approximation in prescribed degree*, Moscow Math. J. 2018.
- Poëls, *On approximation to a real number by algebraic numbers of bounded degree*, Annals of Math. 2025.

**Gap:** AEAS's height-scaling results look under-theorized without connection to approximation exponents. Empirically fitting `log(error)` vs `log(H)` is descriptive; a mathematician reviewer will ask how the observed slope relates to Liouville/Roth-type bounds for algebraic cosines. Confidence: high.

### 2.5 Integer-relation / lattice-reduction baselines

- Lenstra, Lenstra, Lovász, *Factoring Polynomials with Rational Coefficients* (LLL), Math. Ann. 1982.
- Ferguson, Bailey, Arno, *Analysis of PSLQ*, Math. Comp. 1999.
- Bailey & Broadhurst, *Parallel integer relation detection*, Math. Comp. 2001.

**Gap:** PSLQ/LLL-style integer-relation detection over basis `{1, sqrt(m_1), sqrt(m_1 m_2), ...}` is the obvious external baseline for constructible approximation. AEAS does not compare against it. This is the single biggest comparison gap. Confidence: high.

---

## 3. Gap-vs-contribution match

AEAS's four stated contributions mapped against the literature:

1. **Field-first search-system design.** Real but *too loosely framed*. Against Kammerer 2021 and Kahlmeyer 2024, the claim "semantic beats syntactic" is old. A defensible narrow contribution: *bounded-height enumeration in explicit quadratic towers with delayed symbolic materialization* and *diversity-preserving per-sqrt-depth reservation*. Needs reframing in §5.
2. **Reproducible implementation artifact.** Useful, not a scientific contribution on its own. Needs benchmark framing to count.
3. **Depth-vs-height scaling + beam comparison on n∈{7,11,13}.** Weakest. Three targets, method-specific budgets, pooled minima, reversed ordering at higher beam budgets. Descriptive, not a law.
4. **Parameter sweeps.** Appendix material. Currently shaped as "main result." Needs demotion.

---

## 4. Known weaknesses (already self-acknowledged, still load-bearing)

- Method-specific capacity controls (field: height+radicand; beam: node count) — not matched-compute.
- Depth-scaling values are pooled minima across runs; not single-trajectory.
- `q_height <= 14` cap on depth≥2 conflates "algorithm saturation" with "coefficient-denominator cap saturation" — any saturation claim is load-bearing on this.
- No uncertainty intervals, no multi-seed. Runtime variance unbounded.
- Only in-house beam baseline; `field wins 9 of 12 cells` in baseline table but reverses under best-of, and at `n=13, depth∈{2,3}` beam already wins the baseline.
- No completeness/correctness theorem. No complexity lower bound. No connection to Diophantine approximation theory.

---

## 5. Required experiment additions (priority-ordered)

Labels: **[NECESSARY]** = blocker for Q1. **[STRONG]** = strongly recommended. **[NICE]** = upside, not required.

### 5.1 [NECESSARY] Expand the benchmark

All non-Gauss-Wantzel `n` up to 100 or 200. Stratify reports by algebraic degree `phi(n)/2`, prime vs composite, target-value distribution. Turns three anecdotes into a benchmark. Effort: 3–7 days + compute.

### 5.2 [NECESSARY] Matched-compute Pareto curves

Compare field vs beam at *equal walltime*, *equal materialized-candidate count*, *equal mpmath evaluations*, and *equal memory*. Replace win/lose cells with frontier plots: `error vs time`, `error vs node-count`, `error vs evaluations`. Effort: 2–4 days.

### 5.3 [NECESSARY] External baselines

Add, at minimum:
- Continued-fraction / rational best-approximant baseline for depth 0.
- **PSLQ / LLL** over basis `{1, sqrt(m)}` at depth 1 and tower bases at depth ≥ 2 (via `mpmath.pslq` or `fpylll`).
- A tree-GP baseline (PySR or gplearn) with a square-root operator.
- Optional: MCTS over an expression grammar (e.g. Kamienny 2023-style).

Without these, reviewers will reject the RQ2 comparison as in-house-only. Effort: 1–2 weeks.

### 5.4 [NECESSARY] Remove / expose `q_height <= 14` cap

Sweep `q_height ∈ {14, 20, 32, 64}` at depth ≥ 2. Separately label "algorithmic saturation" vs "coefficient-cap saturation" in every depth-scaling plot. Without this, §5.4 of the manuscript (saturation at `H=32` vs `H=64`) is not interpretable. Effort: 2–5 days.

### 5.5 [NECESSARY for math venues] A theorem

Minimum acceptable: exact completeness at depth 1 within stated height/radicand bounds (no false misses from float-prefilter → heap → materialization pipeline) plus complexity bounds for each stage. Stronger: connect the observed `log(error) ~ α·log(H)` slope to a Diophantine approximation exponent for `cos(2π/n)`. Even stronger: lower bound on achievable error at depth `d`, height `H` for a family of `n`. Effort: 1–3 weeks.

### 5.6 [STRONG] Robustness floor

Deterministic pipeline still exhibits hardware-dependent runtime variance — report median + IQR across ≥ 5 hardware runs. For stochastic externals (PySR, MCTS) report multi-seed CIs. Effort: 1–3 days.

### 5.7 [STRONG] Search-landscape characterization beyond heatmaps

Count basins, local-minimum density, canonicalization dedup ratio (how many raw tuples collapse per retained candidate) as a function of depth and `H`. Converts the current qualitative heatmap narrative into a quantitative claim. Effort: 3–5 days.

### 5.8 [NICE] Public benchmark + leaderboard

JSON task format, error-complexity-time Pareto scoring, reference submissions. Unlocks a NeurIPS D&B / AAAI datasets venue. Effort: ~1 week on top of 5.1–5.3.

### 5.9 [NICE] Scale to higher-degree towers or alternative objectives

Non-quadratic extensions; size-penalized objectives; Chebyshev structural filters. Mentioned in current future-work section — pick one and execute it. Effort: 1–2 weeks.

---

## 6. Framing tweaks

- **Retire** "approximating cos(2π/n) for n∈{7,11,13}" as the headline. **Replace with** "bounded-height search over explicit constructible subfields as a benchmark problem for algebraic symbolic search."
- **Retire** "best achievable error" (implies optimality you have not proven). **Replace with** "best verified heuristic error under the stated configuration."
- **Core claim should be architectural:** normal-form field enumeration + delayed symbolic materialization reduces syntactic-redundancy overhead relative to expression-tree generation, quantified by dedup ratio and matched-compute Pareto dominance.
- **Demote parameter sweeps** to appendix. Main paper = benchmark breadth, matched-compute Pareto, one theorem.
- **Position PSLQ/LLL as complementary, not competing:** they find *an* algebraic relation; AEAS finds a *compact constructible expression under a height budget*. Argue this empirically with a Pareto plot.
- **Replace win/loss tables** with frontier plots for multiple `n`: `error vs H`, `error vs nodes`, `error vs walltime`.

---

## 7. Action summary

Minimum to reach a credible Q1 submission: §5.1, §5.2, §5.3, §5.4, §5.5, §5.6 plus the framing tweaks in §6. Realistic effort: **4–8 engineer-weeks** plus compute. Without at least §5.3 (external baselines) and §5.5 (a theorem), this remains an ablation-style systems note.

---

## Appendix A — Methodology for this audit

1. Consensus (peer-reviewed search over Semantic Scholar / PubMed / Scopus / arXiv) queries executed:
   - `symbolic search constructible number approximation quadratic tower algorithm`
   - `nested radicals algebraic approximation enumeration search algorithm`
   - `symbolic regression expression tree beam search canonicalization deduplication`
2. `codex exec` invoked non-interactively with workspace-write sandbox over the full repo, prompted to produce an independent gap analysis, Q1-readiness verdict, and experiment list. Codex performed its own literature sweep in parallel and read `report/aeas_paper.tex`, `report/PLAN.md`, and the `results/analysis/` CSVs directly.
3. Outputs synthesized here; no claim included without at least one independent source (codex or Consensus hit). Denesting citations (Landau/Zippel/Blömer) and deterministic-SR citations (Kammerer 2021, Kahlmeyer 2024) sourced from Consensus; Diophantine-approximation and PSLQ/LLL citations sourced from codex.
