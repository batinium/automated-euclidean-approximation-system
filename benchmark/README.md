# CANB — Constructible Approximation Number Benchmark

Directory layout described in `report/ROADMAP.md`. Spec in `report/benchmark_spec.md`.

## Quick usage

```bash
# regenerate all v0.1 tasks (byte-identical per version+seed)
python scripts/generate_benchmark.py --version 0.1 --seed 20260420 --split all --deterministic

# run AEAS over the transcendental control split
python scripts/run_benchmark.py --method aeas --split canb-transcend --budget '{"walltime_sec":60,"memory_mb":2048,"max_evaluations":null}'

# score submissions
python scripts/score_benchmark.py --method aeas --split canb-transcend
```

## Contributing a new method

1. Implement `solve(task: dict, budget: dict) -> submission: dict` under `src/aeas/baselines/<name>.py`.
2. Register the callable in `src/aeas/methods.py`.
3. Run the harness on `dev` split; open PR with `benchmark/submissions/<name>/<version>/*.json`.
4. CI scores against `test` split and updates the leaderboard.

## Files

- `schema/ast.schema.json` — restricted `aeas-ast-v1` grammar.
- `schema/task.schema.json` — CANB task file schema.
- `schema/submission.schema.json` — method submission schema.
- `MANIFEST.json` — per-task SHA256 + version metadata.
- `tasks/` — generated task files, grouped by family.
- `submissions/` — per-method output JSON files.
- `scores/` — scored CSV files.
