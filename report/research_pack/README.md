# AEAS Literature Research Pack (CS + Math)

This pack is a practical workflow for finding, screening, and citing papers for the AEAS manuscript.
Use it with Zotero and keep all claim-level notes evidence-backed.

## 1) Scope (What to Find)

Target two connected tracks:

- `Math track`: constructibility, quadratic extensions/towers, algebraic number approximation, Diophantine approximation.
- `CS track`: symbolic search, canonicalization/dedup, beam search behavior, symbolic regression, exact/high-precision arithmetic systems, reproducibility in computational math.

Goal: build a paper set that supports
- theorem/background context,
- algorithmic design decisions,
- baseline comparisons,
- evaluation methodology.

## 2) Search Query Pack

Use these in Google Scholar, Semantic Scholar, arXiv, zbMATH, MathSciNet.

### A. Core math (foundations)

- "constructible numbers" straightedge compass quadratic extensions
- "Gauss Wantzel theorem" constructibility regular n-gon
- "quadratic field tower" algebraic numbers
- "nested radicals" algebraic representation
- "Diophantine approximation" algebraic numbers explicit constructions
- "approximation of cos(2pi/n)" algebraic/constructible

### B. Algorithmic math + computation

- "search over algebraic numbers" nested radicals
- "enumeration of algebraic expressions" radicals
- "normal form" algebraic expression canonicalization
- "symbolic simplification" canonical form expression trees
- "PSLQ" algebraic relation detection high precision

### C. CS / symbolic AI / search

- "beam search" symbolic expression generation
- "state-space search" symbolic mathematics
- "symbolic regression" expression tree search operators
- "deduplication canonicalization" program/expression search
- "expression explosion" combinatorial search pruning
- "deterministic reproducible" scientific software experiments

### D. Cross-over / systems framing

- "computer algebra system" exact real arithmetic
- "high precision arithmetic" symbolic numeric hybrid
- "algorithm engineering" search-space reduction symbolic computation
- "reproducibility" computational mathematics experiments

## 3) AI-Assisted Workflow (Strict)

1. Start from 5-10 seed papers (classic + recent).
2. Do backward citation chaining (references of seed papers).
3. Do forward citation chaining (who cited seeds).
4. Use AI only for:
   - query expansion,
   - paper clustering,
   - draft summaries.
5. Verify every strong claim directly from PDF (page/section).
6. Record evidence in `screening_template.csv`.

Rule: no claim enters manuscript unless traceable to at least one verified source line/section.

## 4) Screening Criteria

Include paper if:
- problem is genuinely related (constructibility/algebraic approximation/symbolic search),
- method details are concrete enough to compare,
- contains either theorem-level contribution or reproducible algorithmic evidence.

Exclude paper if:
- only loosely related keyword overlap,
- no method details (high-level opinion/tutorial only),
- no clear link to AEAS design or evaluation.

## 5) Zotero Tagging Scheme

Apply 2-5 tags per paper from below.

- `math-foundation`
- `constructibility`
- `algebraic-number-theory`
- `diophantine-approx`
- `nested-radicals`
- `symbolic-search`
- `beam-search`
- `canonicalization`
- `symbolic-regression`
- `precision-arithmetic`
- `computer-algebra`
- `evaluation-methodology`
- `reproducibility`
- `baseline-candidate`
- `must-cite`

## 6) Mapping Papers to Your Manuscript

- `Introduction/Background`: constructibility theorems, algebraic context.
- `System & Algorithms`: symbolic search methods, canonicalization, pruning.
- `Experimental Setup`: benchmarking and reproducibility standards.
- `Results/Discussion`: prior baseline behavior, complexity/quality tradeoff evidence.
- `Limitations/Future Work`: gaps identified in prior literature.

## 7) Quality-Control Checklist (Before Writing)

- Each major claim has at least one verified citation.
- Foundational theorem claims cite primary/standard references.
- Algorithmic comparisons cite method papers, not just surveys.
- No AI-generated citation without manual verification.
- Bibliography includes both math and CS communities.

## 8) Suggested Weekly Loop

1. Add 15-25 candidates.
2. Screen to 8-12 relevant.
3. Fully read 3-5 high-priority papers.
4. Update manuscript notes with claim-level citations.
5. Mark `must-cite` and `baseline-candidate` in Zotero.
