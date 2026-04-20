"""CANB method adapter for the AEAS field-first search."""

from __future__ import annotations

import math
import multiprocessing as mp
import queue
import time
from importlib import import_module
from dataclasses import dataclass
from typing import Any

import mpmath

from .ast_io import expr_to_ast
from .canb_targets import target_from_spec
from .evaluate import evaluate
from .expr import ExprNode
from .schema_validation import validate_instance


SUBMITTED_AT = "2026-04-20T00:00:00Z"


class _BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class _Budget:
    walltime_sec: float
    memory_mb: float
    max_evaluations: int | None
    max_depth: int
    max_height: int
    max_radicand: int
    max_nodes: int
    beam_width: int
    dps: int
    seed: int
    aeas_q_height_cap: int | None


def solve(task: dict[str, Any], budget: dict[str, Any]) -> dict[str, Any]:
    """Solve one CANB task with AEAS and return a submission dictionary."""
    cfg = _normalize_budget(budget)
    started = time.perf_counter()
    ctx = mp.get_context("fork") if "fork" in mp.get_all_start_methods() else mp
    result_queue: mp.Queue = ctx.Queue(maxsize=1)
    process = ctx.Process(target=_solve_worker, args=(task, cfg, result_queue))
    process.start()
    process.join(cfg.walltime_sec + 0.5)

    if process.is_alive():
        process.terminate()
        process.join(1.0)
        submission = _empty_submission(
            task,
            cfg,
            status="timeout",
            walltime_sec=time.perf_counter() - started,
            notes=f"walltime exceeded {cfg.walltime_sec}s",
        )
    else:
        try:
            submission = result_queue.get_nowait()
        except queue.Empty:
            submission = _empty_submission(
                task,
                cfg,
                status="failed",
                walltime_sec=time.perf_counter() - started,
                notes=f"worker exited with code {process.exitcode}",
            )

    submission["metrics"]["walltime_sec"] = min(
        float(submission["metrics"]["walltime_sec"]),
        cfg.walltime_sec + 0.5,
    )
    validate_instance(submission, "submission.schema.json")
    return submission


def _solve_worker(
    task: dict[str, Any],
    cfg: _Budget,
    result_queue: mp.Queue,
) -> None:
    field_module = import_module("aeas.field_search")

    started = time.perf_counter()
    target = target_from_spec(task["target_spec"], cfg.dps)
    eval_count = 0
    original_evaluate = field_module.evaluate

    def counted_evaluate(expr: ExprNode, dps: int = 80):
        nonlocal eval_count
        if time.perf_counter() - started > cfg.walltime_sec:
            raise _BudgetExceeded(f"walltime exceeded {cfg.walltime_sec}s")
        eval_count += 1
        if cfg.max_evaluations is not None and eval_count > cfg.max_evaluations:
            raise _BudgetExceeded(
                f"max_evaluations exceeded {cfg.max_evaluations}"
            )
        return original_evaluate(expr, dps)

    field_module.evaluate = counted_evaluate
    try:
        results = field_module.field_search(
            target=target,
            n_val=_n_hint(task),
            max_depth=cfg.max_depth,
            max_height=cfg.max_height,
            max_radicand=cfg.max_radicand,
            max_nodes=cfg.max_nodes,
            beam_width=cfg.beam_width,
            dps=cfg.dps,
            seed=cfg.seed,
            progress=False,
        )
        best = _best_candidate(results)
        if best is None:
            submission = _empty_submission(
                task,
                cfg,
                status="failed",
                walltime_sec=time.perf_counter() - started,
                notes="AEAS returned no valid candidates",
            )
        else:
            err, expr = best
            submission = _success_submission(
                task=task,
                cfg=cfg,
                expr=expr,
                error=err,
                walltime_sec=time.perf_counter() - started,
                eval_count=eval_count,
            )
    except _BudgetExceeded as exc:
        submission = _empty_submission(
            task,
            cfg,
            status="timeout",
            walltime_sec=time.perf_counter() - started,
            notes=str(exc),
        )
        submission["metrics"]["num_evaluations"] = eval_count
    except Exception as exc:
        submission = _empty_submission(
            task,
            cfg,
            status="failed",
            walltime_sec=time.perf_counter() - started,
            notes=f"{type(exc).__name__}: {exc}",
        )
        submission["metrics"]["num_evaluations"] = eval_count
    finally:
        field_module.evaluate = original_evaluate

    result_queue.put(submission)


def _best_candidate(
    results: dict[int, list[tuple[float, ExprNode]]],
) -> tuple[float, ExprNode] | None:
    candidates = [entry for entries in results.values() for entry in entries]
    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1].node_count, item[1].to_str()))


def _success_submission(
    task: dict[str, Any],
    cfg: _Budget,
    expr: ExprNode,
    error: float,
    walltime_sec: float,
    eval_count: int,
) -> dict[str, Any]:
    value = evaluate(expr, 80)
    target80 = target_from_spec(task["target_spec"], 80)
    if value is None:
        error_text = "inf"
    else:
        error_text = mpmath.nstr(abs(value - target80), 12)
    notes = "AEAS field-first adapter"
    if cfg.aeas_q_height_cap is not None:
        notes = f"{notes}; aeas_q_height_cap={cfg.aeas_q_height_cap}"
    return {
        "task_id": task["id"],
        "method": "aeas",
        "submitted_at": SUBMITTED_AT,
        "status": "success",
        "budget": _budget_payload(cfg),
        "metrics": {
            "walltime_sec": float(walltime_sec),
            "peak_memory_mb": 0.0,
            "num_evaluations": eval_count,
        },
        "expression": {
            "format": "aeas-ast-v1",
            "ast": expr_to_ast(expr),
        },
        "error_selfreport_dps80": error_text if math.isfinite(error) else "inf",
        "notes": notes,
    }


def _empty_submission(
    task: dict[str, Any],
    cfg: _Budget,
    status: str,
    walltime_sec: float,
    notes: str,
) -> dict[str, Any]:
    return {
        "task_id": task["id"],
        "method": "aeas",
        "submitted_at": SUBMITTED_AT,
        "status": status,
        "budget": _budget_payload(cfg),
        "metrics": {
            "walltime_sec": float(walltime_sec),
            "peak_memory_mb": 0.0,
            "num_evaluations": 0,
        },
        "expression": None,
        "error_selfreport_dps80": None,
        "notes": notes,
    }


def _normalize_budget(raw: dict[str, Any]) -> _Budget:
    walltime_sec = float(
        raw.get("walltime_sec", raw.get("max_walltime_sec", 60.0))
    )
    memory_mb = float(raw.get("memory_mb", raw.get("max_memory_mb", 2048.0)))
    max_evaluations = raw.get("max_evaluations")
    if max_evaluations is not None:
        max_evaluations = int(max_evaluations)

    beam_width = int(raw.get("beam_width", 800 if walltime_sec >= 30 else 300))
    max_height = int(raw.get("max_height", 16 if walltime_sec >= 30 else 10))
    max_depth = int(raw.get("max_depth", 2 if walltime_sec >= 10 else 1))
    max_radicand = int(raw.get("max_radicand", 24 if walltime_sec >= 30 else 12))
    q_height_cap = raw.get("aeas_q_height_cap")
    if q_height_cap is not None:
        q_height_cap = max(1, int(q_height_cap))

    if memory_mb <= 512:
        beam_width = min(beam_width, 250)
        max_height = min(max_height, 10)
    elif memory_mb <= 1024:
        beam_width = min(beam_width, 500)
        max_height = min(max_height, 14)

    if q_height_cap is not None and max_depth >= 2:
        max_height = min(max_height, q_height_cap)

    return _Budget(
        walltime_sec=max(walltime_sec, 0.1),
        memory_mb=max(memory_mb, 1.0),
        max_evaluations=max_evaluations,
        max_depth=max_depth,
        max_height=max_height,
        max_radicand=max_radicand,
        max_nodes=int(raw.get("max_nodes", 50)),
        beam_width=max(1, beam_width),
        dps=int(raw.get("dps", 80)),
        seed=int(raw.get("seed", 42)),
        aeas_q_height_cap=q_height_cap,
    )


def _budget_payload(cfg: _Budget) -> dict[str, Any]:
    return {
        "max_walltime_sec": cfg.walltime_sec,
        "max_memory_mb": cfg.memory_mb,
        "max_evaluations": cfg.max_evaluations,
    }


def _n_hint(task: dict[str, Any]) -> int:
    spec = task.get("target_spec", {})
    if spec.get("kind") == "cos_of_rational_pi":
        arg = spec.get("arg", [0, 0])
        if arg[0] == 2:
            return int(arg[1])
    return 0
