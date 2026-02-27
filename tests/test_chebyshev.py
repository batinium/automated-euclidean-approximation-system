"""Tests for Chebyshev polynomial evaluation."""

import math

import mpmath
import pytest

from aeas.chebyshev import chebyshev_T, chebyshev_T_float, chebyshev_residual
from aeas.evaluate import compute_target


class TestChebyshevT:
    def test_T0(self):
        assert float(chebyshev_T(0, mpmath.mpf(0.5), dps=30)) == pytest.approx(1.0)

    def test_T1(self):
        assert float(chebyshev_T(1, mpmath.mpf(0.7), dps=30)) == pytest.approx(0.7)

    def test_T2(self):
        x = 0.6
        expected = 2 * x**2 - 1
        assert float(chebyshev_T(2, mpmath.mpf(x), dps=30)) == pytest.approx(expected)

    def test_T3(self):
        x = 0.4
        expected = 4 * x**3 - 3 * x
        assert float(chebyshev_T(3, mpmath.mpf(x), dps=30)) == pytest.approx(expected)

    def test_Tn_cos_identity(self):
        """T_n(cos θ) = cos(nθ) for various n and θ."""
        for n in (5, 7, 11):
            theta = 0.3
            x = math.cos(theta)
            expected = math.cos(n * theta)
            got = float(chebyshev_T(n, mpmath.mpf(x), dps=30))
            assert got == pytest.approx(expected, abs=1e-12)


class TestChebyshevTargetIdentity:
    """T_n(cos(2π/n)) = cos(2π) = 1 for non-constructible n."""

    @pytest.mark.parametrize("n", [7, 11, 13, 17, 19])
    def test_Tn_at_target_is_one(self, n):
        target = compute_target(n, dps=50)
        result = chebyshev_T(n, target, dps=50)
        assert abs(float(result) - 1.0) < 1e-40


class TestChebyshevFloat:
    def test_agrees_with_mpmath(self):
        for n in (3, 7, 13):
            x = 0.55
            mp_val = float(chebyshev_T(n, mpmath.mpf(x), dps=30))
            fl_val = chebyshev_T_float(n, x)
            assert fl_val == pytest.approx(mp_val, abs=1e-12)

    def test_T0_float(self):
        assert chebyshev_T_float(0, 0.5) == 1.0

    def test_T1_float(self):
        assert chebyshev_T_float(1, 0.7) == pytest.approx(0.7)


class TestChebyshevResidual:
    def test_residual_near_target(self):
        target = compute_target(7, dps=50)
        assert chebyshev_residual(7, target, dps=50) < 1e-40

    def test_residual_far_from_target(self):
        assert chebyshev_residual(7, mpmath.mpf(0.0), dps=30) > 0.1

    def test_residual_positive(self):
        assert chebyshev_residual(11, mpmath.mpf(0.3), dps=30) >= 0
