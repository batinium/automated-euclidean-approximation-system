"""Tests for arbitrary-precision expression evaluation."""

import pytest
import mpmath
from fractions import Fraction

from aeas.expr import ExprNode, Op
from aeas.evaluate import evaluate, compute_target, clear_cache


def _c(v) -> ExprNode:
    return ExprNode(Op.CONST, value=Fraction(v))


@pytest.fixture(autouse=True)
def _reset_cache():
    clear_cache()
    yield
    clear_cache()


class TestBasicEval:
    def test_integer(self):
        assert abs(float(evaluate(_c(3), dps=30)) - 3.0) < 1e-25

    def test_fraction(self):
        val = evaluate(_c(Fraction(1, 3)), dps=50)
        with mpmath.workdps(55):
            expected = mpmath.mpf(1) / 3
        assert abs(float(val) - float(expected)) < 1e-45

    def test_add(self):
        e = ExprNode(Op.ADD, children=(_c(1), _c(2)))
        assert abs(float(evaluate(e, dps=30)) - 3.0) < 1e-25

    def test_sub(self):
        e = ExprNode(Op.SUB, children=(_c(5), _c(3)))
        assert abs(float(evaluate(e, dps=30)) - 2.0) < 1e-25

    def test_mul(self):
        e = ExprNode(Op.MUL, children=(_c(3), _c(4)))
        assert abs(float(evaluate(e, dps=30)) - 12.0) < 1e-25

    def test_div(self):
        e = ExprNode(Op.DIV, children=(_c(7), _c(2)))
        assert abs(float(evaluate(e, dps=30)) - 3.5) < 1e-25


class TestSqrt:
    def test_perfect_square(self):
        e = ExprNode(Op.SQRT, children=(_c(4),))
        assert abs(float(evaluate(e, dps=30)) - 2.0) < 1e-25

    def test_irrational(self):
        e = ExprNode(Op.SQRT, children=(_c(2),))
        val = evaluate(e, dps=50)
        with mpmath.workdps(55):
            expected = mpmath.sqrt(2)
        assert abs(float(val) - float(expected)) < 1e-45


class TestSafetyChecks:
    def test_div_by_zero(self):
        e = ExprNode(Op.DIV, children=(_c(1), _c(0)))
        assert evaluate(e, dps=30) is None

    def test_sqrt_negative(self):
        e = ExprNode(Op.SQRT, children=(_c(-1),))
        assert evaluate(e, dps=30) is None

    def test_nested_invalid_propagates(self):
        bad = ExprNode(Op.SQRT, children=(_c(-4),))
        e = ExprNode(Op.ADD, children=(bad, _c(1)))
        assert evaluate(e, dps=30) is None


class TestComputeTarget:
    def test_cos_pi_over_2(self):
        t = compute_target(4, dps=30)
        assert abs(float(t)) < 1e-25  # cos(π/2) = 0

    def test_cos_2pi_over_6(self):
        t = compute_target(6, dps=30)
        assert abs(float(t) - 0.5) < 1e-25  # cos(60°) = 1/2

    def test_cos_2pi_over_3(self):
        t = compute_target(3, dps=30)
        assert abs(float(t) - (-0.5)) < 1e-25  # cos(120°) = -1/2


class TestNested:
    def test_golden_ratio_half(self):
        # (1 + sqrt(5)) / 4 ≈ 0.80902
        inner = ExprNode(Op.SQRT, children=(_c(5),))
        num = ExprNode(Op.ADD, children=(_c(1), inner))
        e = ExprNode(Op.DIV, children=(num, _c(4)))
        val = evaluate(e, dps=30)
        assert val is not None
        assert abs(float(val) - 0.80902) < 1e-4
