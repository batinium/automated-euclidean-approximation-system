# Resume Prompt — AEAS → CANB Q1 Audit

Paste the block below into Claude Code (or any coding agent) to continue the
research-direction audit of the CANB reframing for
`/Users/bato/MyProjects/automated-euclidean-approximation-system`.

This prompt is self-contained. Everything else lives in the repo.

---

## Resume block (copy-paste)

```
You are continuing a research-direction audit that a prior Claude agent started
on 2026-04-20. The target venue class is Q1 computational-math / CS (primary:
Journal of Symbolic Computation; parallel: ISSAC 2027; fallback: NeurIPS D&B
or Experimental Mathematics). The original paper (hand-crafted tridecagon
approximation) was rejected for being too niche; we have reframed as CANB, a
benchmark for bounded-height constructible approximation of real numbers, with
AEAS as the reference method.

STEP 1 — Boot from the tracker.
Read, in order:
  report/AUDIT.md                   <-- master tracker; source of truth
  report/OVERVIEW.md                <-- plain-language summary
  report/PLAN.md                    <-- strategy + locked decisions (§11)
  report/EXPERIMENTS.md             <-- experiment narrative
  report/STATUS.md                  <-- audit log; tail first
  audit.md                          <-- historical critical review

STEP 2 — Confirm baseline.
Run:
  /Users/bato/micromamba/envs/aeas/bin/python -m pytest tests/ -q
Expected: 150+ passed. If not, STOP and report.

STEP 3 — Identify next task.
Open report/AUDIT.md §7 "Progress Log". The most recent entry names the next
scheduled action (a §9.X codex directive). Execute that directive.

STEP 4 — Run codex.
Codex directives live in report/AUDIT.md §9 (§9.A through §9.H). Each is
self-contained. Invoke codex with:
  codex exec --sandbox <mode> --full-auto --skip-git-repo-check \
    -C /Users/bato/MyProjects/automated-euclidean-approximation-system \
    -m gpt-5.4 --config model_reasoning_effort="high" \
    "$(cat <<'PROMPT'
    <paste directive body here>
    PROMPT
    )" 2>/dev/null

Sandbox:
  - read-only for audits (§9.A, §9.G)
  - workspace-write for code tasks (§9.B, §9.C, §9.D, §9.E, §9.F, §9.H)
  - danger-full-access only when network is required (Consensus MCP,
    Julia/PySR bootstrap, fpylll download)

STEP 5 — Audit codex output.
Do NOT assume codex is correct. Check claims against current repo state.
For citations, grep the existing bibliography to avoid duplicate bibkeys.
For code edits, run pytest and inspect diffs before trusting "done."
Record your verification inline under the new section codex wrote.

STEP 6 — Log progress.
Append an entry to report/AUDIT.md §7 with:
  - Date (ISO 8601)
  - What was done (which §9.X directive)
  - Test count delta
  - Follow-up / next scheduled action

STEP 7 — Commit + push.
Only if user explicitly asks. Use a single commit per logical deliverable. No
auto-commit mid-task.

HARD RULES
- Do NOT delete results/ or report/archive/.
- Do NOT modify src/aeas/{expr, canonicalize, evaluate, field_search, search,
  chebyshev}.py beyond adding public helpers — UNLESS the directive is §9.D
  (q_height cap lift), in which case flag the lock break in the commit msg.
- Do NOT auto-commit.
- Do NOT write emojis in files.
- Seed every RNG path. No wall-clock randomness in benchmark generator or
  scorer.

VENUE DECISION TREE (from AUDIT.md §4)
  theorem drafted AND frontier plots clean?
    YES -> JSC primary, arXiv preprint day 1, ISSAC 2027 short 6 mo later
    NO  -> NeurIPS D&B 2026, Experimental Mathematics as fallback

KILL-SWITCH TRIGGERS
- PSLQ Pareto-dominates AEAS everywhere -> reframe "when is PSLQ not enough"
- Theorem blocks > 5 days -> drop to NeurIPS D&B or Experimental Mathematics
- Compute > 2 core-weeks per method -> shrink benchmark or drop slowest
  baseline

START HERE
Open report/AUDIT.md §7 and read the last progress-log entry. Do what it says.
```

---

## Invocation helpers

```bash
# boot claude code from repo root
cd /Users/bato/MyProjects/automated-euclidean-approximation-system
claude

# then paste the Resume block above
```

To resume the most recent codex session (same model/reasoning/sandbox):

```bash
echo "continue the last codex task; read report/AUDIT.md §7 for context" \
  | codex exec --skip-git-repo-check resume --last 2>/dev/null
```

---

## State snapshot at save time (2026-04-20)

- Tests: 150 passed
- Tasks generated: 222 (canb-poly 167, canb-trig 50, canb-transcend 5)
- Scored: AEAS, CF, PSLQ on canb-poly + canb-transcend
- §2.H (positioning sweep) done; §5.1 in AUDIT.md lists 10 papers + verdicts
- Next scheduled: §9.C matched-compute frontier + plot_frontier.py
