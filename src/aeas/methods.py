"""Method registry for the CANB harness."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .baselines.cf import solve as cf_solve
from .baselines.pslq import solve as pslq_solve
from .canb_adapter import solve as aeas_solve

Method = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


METHODS: dict[str, Method] = {
    "aeas": aeas_solve,
    "cf": cf_solve,
    "pslq": pslq_solve,
}


def get_method(name: str) -> Method:
    try:
        return METHODS[name]
    except KeyError as exc:
        available = ", ".join(sorted(METHODS))
        raise KeyError(f"unknown method {name!r}; available: {available}") from exc
