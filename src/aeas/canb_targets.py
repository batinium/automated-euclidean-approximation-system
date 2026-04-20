"""Target evaluation helpers for CANB tasks."""

from __future__ import annotations

import math
from typing import Any

import mpmath


FERMAT_PRIMES = (3, 5, 17, 257, 65537)
TRANSCENDENTAL_NAMES = ("pi", "e", "ln2", "euler_gamma", "apery_zeta_3")


def is_gauss_wantzel(n: int) -> bool:
    """Return whether a regular n-gon is ruler-and-compass constructible."""
    if n < 1:
        return False
    while n % 2 == 0:
        n //= 2
    for prime in FERMAT_PRIMES:
        if n % prime == 0:
            n //= prime
            if n % prime == 0:
                return False
    return n == 1


def target_from_spec(target_spec: dict[str, Any], dps: int = 1000) -> mpmath.mpf:
    """Evaluate a CANB target specification to *dps* decimal places."""
    kind = target_spec["kind"]
    with mpmath.workdps(dps + 100):
        if kind in {
            "cos_of_rational_pi",
            "sin_of_rational_pi",
            "tan_of_rational_pi",
        }:
            p, q = target_spec["arg"]
            angle = mpmath.mpf(p) * mpmath.pi / mpmath.mpf(q)
            if kind == "cos_of_rational_pi":
                return +mpmath.cos(angle)
            if kind == "sin_of_rational_pi":
                return +mpmath.sin(angle)
            return +mpmath.tan(angle)

        if kind == "literal_transcendental":
            name = target_spec["name"]
            if name == "pi":
                return +mpmath.pi
            if name == "e":
                return +mpmath.e
            if name == "ln2":
                return +mpmath.log(2)
            if name == "euler_gamma":
                return +mpmath.euler
            if name in {"apery", "apery_zeta_3"}:
                return +mpmath.zeta(3)

        if kind == "root_of_polynomial":
            roots = mpmath.polyroots(
                [mpmath.mpf(c) for c in target_spec["coefficients"]],
                maxsteps=200,
                error=False,
            )
            tolerance = mpmath.mpf(10) ** (-(dps // 2))
            real_roots = sorted(
                [mpmath.re(root) for root in roots if abs(mpmath.im(root)) < tolerance]
            )
            idx = target_spec["real_root_index"]
            if idx < len(real_roots):
                return +real_roots[idx]
            raise ValueError(
                f"real_root_index {idx} out of range for {len(real_roots)} real roots"
            )

    raise ValueError(f"unsupported target_spec kind/name: {target_spec!r}")


def decimal_truncate(value: mpmath.mpf, digits_after_decimal: int = 1000) -> str:
    """Return a fixed-point decimal string truncated, not rounded."""
    with mpmath.workdps(digits_after_decimal + 100):
        x = mpmath.mpf(value)
        sign = "-" if x < 0 else ""
        x = abs(x)
        int_part = int(mpmath.floor(x))
        scale = mpmath.mpf(10) ** digits_after_decimal
        frac_part = int(mpmath.floor((x - int_part) * scale))
        return f"{sign}{int_part}.{frac_part:0{digits_after_decimal}d}"


def reduced_coprime(p: int, q: int) -> bool:
    return math.gcd(p, q) == 1
