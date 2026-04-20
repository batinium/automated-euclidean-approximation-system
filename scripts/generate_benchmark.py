#!/usr/bin/env python
"""Generate deterministic CANB v0.1 task files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import mpmath

_root = Path(__file__).resolve().parent.parent
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from aeas.canb_targets import (  # noqa: E402
    TRANSCENDENTAL_NAMES,
    decimal_truncate,
    is_gauss_wantzel,
    reduced_coprime,
    target_from_spec,
)
from aeas.schema_validation import validate_instance  # noqa: E402


SUPPORTED_SPLITS = ("canb-poly", "canb-trig", "canb-transcend")
MANIFEST_TIMESTAMP = "2026-04-20T00:00:00Z"
REFERENCE_DPS = 1000
COMPUTE_DPS = 1100


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--split",
        choices=[*SUPPORTED_SPLITS, "all"],
        required=True,
    )
    parser.add_argument("--out", type=Path, default=Path("benchmark/tasks"))
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Use the fixed manifest timestamp required for reproducible diffs.",
    )
    args = parser.parse_args()

    selected = list(SUPPORTED_SPLITS) if args.split == "all" else [args.split]
    tasks: list[dict[str, Any]] = []
    for family in selected:
        if family == "canb-poly":
            tasks.extend(generate_poly_tasks())
        elif family == "canb-trig":
            tasks.extend(generate_trig_tasks())
        elif family == "canb-transcend":
            tasks.extend(generate_transcend_tasks())

    write_tasks(
        tasks=tasks,
        out_dir=args.out,
        selected_families=selected,
        version=args.version,
        seed=args.seed,
        deterministic=args.deterministic,
    )


def generate_poly_tasks() -> list[dict[str, Any]]:
    tasks = []
    for n in range(7, 201):
        if is_gauss_wantzel(n):
            continue
        spec = {"kind": "cos_of_rational_pi", "arg": [2, n]}
        tasks.append(
            _task(
                task_id=f"canb-poly-n{n}",
                family="canb-poly",
                target_description=f"cos(2*pi/{n})",
                target_spec=spec,
                difficulty_tier=2,
                notes=f"non-Gauss-Wantzel n={n}",
            )
        )
    return tasks


def generate_trig_tasks() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    with mpmath.workdps(COMPUTE_DPS):
        for q in range(7, 41):
            if is_gauss_wantzel(q):
                continue
            for p in range(1, q):
                if not reduced_coprime(p, q):
                    continue
                for fn in ("sin", "tan"):
                    kind = f"{fn}_of_rational_pi"
                    spec = {"kind": kind, "arg": [p, q]}
                    target = target_from_spec(spec, COMPUTE_DPS)
                    if fn == "sin" and not (-1 < target < 1):
                        continue
                    if fn == "tan" and not (
                        mpmath.isfinite(target) and -10 < target < 10
                    ):
                        continue
                    candidates.append(
                        _task(
                            task_id=f"canb-trig-{fn}-p{p}-q{q}",
                            family="canb-trig",
                            target_description=f"{fn}({p}*pi/{q})",
                            target_spec=spec,
                            difficulty_tier=2,
                            notes=f"reduced rational angle with non-Gauss-Wantzel q={q}",
                        )
                    )
    return sorted(
        candidates,
        key=lambda task: (
            task["target_spec"]["arg"][1],
            task["target_spec"]["arg"][0],
            task["target_spec"]["kind"],
        ),
    )[:50]


def generate_transcend_tasks() -> list[dict[str, Any]]:
    descriptions = {
        "pi": "pi",
        "e": "e",
        "ln2": "ln(2)",
        "euler_gamma": "Euler-Mascheroni gamma",
        "apery_zeta_3": "Apery's constant zeta(3)",
    }
    return [
        _task(
            task_id=f"canb-transcend-{name.replace('_', '-')}",
            family="canb-transcend",
            target_description=descriptions[name],
            target_spec={"kind": "literal_transcendental", "name": name},
            difficulty_tier=4,
            notes="transcendental/control target",
        )
        for name in TRANSCENDENTAL_NAMES
    ]


def write_tasks(
    tasks: list[dict[str, Any]],
    out_dir: Path,
    selected_families: list[str],
    version: str,
    seed: int,
    deterministic: bool,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for family in selected_families:
        family_dir = out_dir / family
        if family_dir.exists():
            shutil.rmtree(family_dir)
        family_dir.mkdir(parents=True, exist_ok=True)

    manifest_tasks = []
    for task in sorted(tasks, key=lambda item: item["id"]):
        validate_instance(task, "task.schema.json")
        path = out_dir / task["family"] / f"{task['id']}.json"
        payload = json.dumps(task, indent=2, sort_keys=True) + "\n"
        path.write_text(payload)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        manifest_tasks.append(
            {
                "id": task["id"],
                "family": task["family"],
                "path": str(path.relative_to(out_dir.parent)),
                "sha256": digest,
            }
        )

    manifest = {
        "benchmark": "CANB",
        "generator": "scripts/generate_benchmark.py",
        "version": version,
        "seed": seed,
        "split": "all" if len(selected_families) == len(SUPPORTED_SPLITS) else selected_families[0],
        "timestamp": MANIFEST_TIMESTAMP,
        "deterministic": deterministic,
        "task_count": len(manifest_tasks),
        "tasks": manifest_tasks,
    }
    manifest_path = out_dir.parent / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(manifest_tasks)} tasks to {out_dir}")
    print(f"wrote manifest to {manifest_path}")


def _task(
    task_id: str,
    family: str,
    target_description: str,
    target_spec: dict[str, Any],
    difficulty_tier: int,
    notes: str,
) -> dict[str, Any]:
    value = target_from_spec(target_spec, COMPUTE_DPS)
    return {
        "id": task_id,
        "family": family,
        "target_description": target_description,
        "target_spec": target_spec,
        "reference_value_dps": REFERENCE_DPS,
        "reference_value": decimal_truncate(value, REFERENCE_DPS),
        "known_closed_form": None,
        "difficulty_tier": difficulty_tier,
        "notes": notes,
    }


if __name__ == "__main__":
    main()
