"""Chebyshev polynomial evaluation for AEAS.

For target α = cos(2π/n), the identity T_n(α) = cos(2π) = 1 provides a
structurally meaningful error signal.  |T_n(x) − 1| amplifies deviations
from the target in a way that respects the cyclotomic geometry.
"""

from __future__ import annotations

import mpmath


def chebyshev_T(n: int, x: mpmath.mpf, dps: int = 80) -> mpmath.mpf:
    """Evaluate the Chebyshev polynomial T_n(x) at arbitrary precision.

    Uses the three-term recurrence T_0=1, T_1=x, T_{k+1}=2xT_k − T_{k−1}.
    """
    with mpmath.workdps(dps + 15):
        x = mpmath.mpf(x) if not isinstance(x, mpmath.mpf) else x
        if n == 0:
            return mpmath.mpf(1)
        if n == 1:
            return +x
        t0, t1 = mpmath.mpf(1), x
        for _ in range(2, n + 1):
            t0, t1 = t1, 2 * x * t1 - t0
        return +t1


def chebyshev_T_float(n: int, x: float) -> float:
    """Fast float-precision T_n(x) for pre-filtering large candidate sets."""
    if n == 0:
        return 1.0
    if n == 1:
        return x
    t0, t1 = 1.0, x
    for _ in range(2, n + 1):
        t0, t1 = t1, 2.0 * x * t1 - t0
    return t1


def chebyshev_residual(n: int, x: mpmath.mpf, dps: int = 80) -> float:
    """Return |T_n(x) − 1|.  Small when x ≈ cos(2π/n)."""
    return abs(float(chebyshev_T(n, x, dps) - 1))
