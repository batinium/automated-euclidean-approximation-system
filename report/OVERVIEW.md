# Project Overview (Plain-Language)

*Use this as the one-page explanation when someone asks "what is this research about?"*

---

## The original problem

You want to draw a regular 13-gon (or 7-gon, or 11-gon) with just ruler and compass. You can't — Gauss and Wantzel proved in the 1800s that most regular polygons are geometrically impossible to construct exactly. But you can get arbitrarily close using only the shapes a ruler and compass *can* draw: line segments, circles, and nested square roots of rational numbers (those are called **constructible numbers**).

So the question becomes: given a target number like `cos(2π/13) = 0.5680647…`, what's the best constructible expression that approximates it, under some budget on how large and nested the expression is allowed to be?

Example: `cos(2π/7) ≈ (1/6) * (−1 + √(7) + √(3 + √(7)·something))` — a specific nested-radical recipe.

## What your original paper did

Built a search algorithm (AEAS) that finds good constructible approximations automatically, tested it on n = 7, 11, 13. It worked. But reviewers kept rejecting it because "only three polygons" is too narrow a problem for a general CS/math venue.

## The reframing — what you're actually doing now

You're not writing a paper about 13-gons anymore. You're writing a paper that says:

> "**Nobody has a standard test set for the general problem of searching for compact algebraic approximations to real numbers. I'm making one, and here's how six different methods perform on it.**"

That's the switch. You go from "I solved a niche puzzle" to "I defined a general evaluation playing field and populated it with contestants."

## The framework (CANB) in plain terms

Think of it like **SAT benchmarks for SAT solvers**, or **ImageNet for image classifiers**, but for a much smaller niche: algorithms that hunt for compact nested-square-root expressions matching a given real number.

The framework has four pieces:

1. **Tasks.** A few hundred real numbers you want to approximate — polygon cosines, roots of polynomials, π, e, some textbook nested radicals. Each task is a small JSON file with the target value to 1000 digits and some metadata.

2. **Submission format.** Every participating algorithm outputs its answer as a standardized expression tree (a JSON AST describing the radical it found).

3. **Scoring.** Three things matter simultaneously: (a) how close to the target, (b) how short the expression, (c) how long the algorithm took. Combined via a standard multi-objective metric (Pareto hypervolume).

4. **Contestants.** Six methods implemented and run against every task:
   - **AEAS** — your algorithm, the main character.
   - **Continued fractions** — the obvious dumb baseline (no square roots, just p/q).
   - **PSLQ** — a classical integer-relation finder from computational number theory.
   - **LLL** — lattice reduction, another classical tool.
   - **PySR** — a state-of-the-art symbolic regression library from the ML community.
   - **Local LLMs** — modern language models given the problem as a prompt; see what they do.

## What you're hoping to show

Not "my method beats everyone everywhere" (unrealistic, and reviewers distrust it). Instead:

> "Different methods win in different regimes. Here's a clean benchmark that shows when and why."

Specifically the expected story:

- AEAS wins on **structured** targets (polygon cosines, Ramanujan-style radicals) — because the field-first search exploits the structure.
- PSLQ wins when the target has an **exact** closed-form hiding inside your chosen basis.
- Tree-based symbolic regression wins on **random-looking** targets where no structure helps.
- Continued fractions are the cheapest safe floor.
- LLMs are a wildcard — probably weak on hard tasks, possibly surprising on easy ones.

That story is publishable whether AEAS dominates or not.

## What makes it publishable at Q1

Three reasons combined:

1. **It's a benchmark.** Benchmarks are valued — they enable future work by others. Good benchmarks get cited for years.
2. **It's reproducible.** All tasks regenerate from a seed. All methods have open code. All scoring is automated.
3. **It says something true.** The complementary-regimes finding is more honest and more useful than "my method wins."

The reference AEAS method and the small completeness theorem add substance. Without a benchmark those alone weren't enough; with a benchmark they become the central piece of infrastructure that justifies the benchmark existing.

## Your one-sentence elevator pitch

> "I built the first standardized benchmark for bounded-height algebraic approximation search, implemented a field-first reference method and five external baselines, and showed which method wins in which target regime."

Keep that sentence. Use it in the abstract, in the advisor email, in any cold outreach after preprint.

## What's next, practically

Week 1 of `report/ROADMAP.md`:

1. Freeze the task JSON schema.
2. Write `scripts/generate_benchmark.py` — emits the ~125 v0.1 tasks.
3. Adapt AEAS to the harness (one small adapter file).
4. First end-to-end run: generate tasks → AEAS solves them → scorer produces a CSV.

That first end-to-end pipeline is the hardest psychological step. Everything after is bolting on baselines and plotting.

## Where to look when confused

- `report/PLAN.md` — strategy, phases, locked decisions.
- `report/ROADMAP.md` — week-by-week actionable checklist.
- `report/benchmark_spec.md` — exact schema, scoring formulas, rules.
- `report/aeas_paper.tex` — current paper skeleton to be filled in.
- `audit.md` — the critical review that motivated the reframing.
- `report/archive/` — v1 artifacts (old plan + old paper draft), kept for reproducibility.

---

## Final closure checklist before wiping this chat

- [x] Decisions locked in `PLAN.md` §11 (benchmark size, local LLMs, JSC primary, advisor co-author path).
- [x] LLM baseline swapped from Anthropic API to local via Ollama/vLLM.
- [x] Old paper + plan archived; new skeleton + spec + roadmap in place.
- [x] `README.md` rewritten for CANB framing.
- [x] `audit.md` preserved as historical record.
- [x] Elevator-pitch sentence recorded above.
- [ ] Pending: kick off Week 1 of `ROADMAP.md`.
- [ ] Pending: advisor meeting.
