"""Tests for the field-first search module."""

import math
from fractions import Fraction

import mpmath
import pytest

from aeas.evaluate import clear_cache, compute_target, evaluate
from aeas.expr import ExprNode, Op
from aeas.field_search import (
    _best_rational_approx,
    _bounded_rationals,
    _make_correction_tree,
    _make_depth1_tree,
    _make_nested_tree,
    _squarefree_up_to,
    field_search,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    clear_cache()
    yield
    clear_cache()


# ── utility functions ────────────────────────────────────────────────


class TestSquarefree:
    def test_small(self):
        sf = _squarefree_up_to(10)
        assert sf == [2, 3, 5, 6, 7, 10]

    def test_excludes_squares(self):
        sf = _squarefree_up_to(30)
        for n in sf:
            for p in range(2, n):
                assert n % (p * p) != 0

    def test_limit_zero(self):
        assert _squarefree_up_to(0) == []

    def test_limit_one(self):
        assert _squarefree_up_to(1) == []


class TestBoundedRationals:
    def test_contains_integers(self):
        rats = _bounded_rationals(3, lo=-3, hi=3)
        for i in range(-3, 4):
            assert Fraction(i) in rats

    def test_contains_unit_fractions(self):
        rats = _bounded_rationals(4, lo=0, hi=1)
        assert Fraction(1, 2) in rats
        assert Fraction(1, 3) in rats
        assert Fraction(1, 4) in rats

    def test_sorted_by_value(self):
        rats = _bounded_rationals(5, lo=-1, hi=1)
        for i in range(len(rats) - 1):
            assert float(rats[i]) <= float(rats[i + 1])

    def test_all_reduced(self):
        rats = _bounded_rationals(10, lo=-1, hi=1)
        for r in rats:
            assert math.gcd(abs(r.numerator), r.denominator) == 1


class TestBestRationalApprox:
    def test_exact_integer(self):
        assert _best_rational_approx(3.0, 10) == Fraction(3)

    def test_exact_half(self):
        assert _best_rational_approx(0.5, 10) == Fraction(1, 2)

    def test_pi_approx(self):
        best = _best_rational_approx(math.pi, 100)
        assert abs(float(best) - math.pi) < 0.004  # 355/113 at denom 113

    def test_improves_with_higher_denom(self):
        err1 = abs(float(_best_rational_approx(math.sqrt(2), 10)) - math.sqrt(2))
        err2 = abs(float(_best_rational_approx(math.sqrt(2), 100)) - math.sqrt(2))
        assert err2 <= err1


# ── tree builders ────────────────────────────────────────────────────


class TestMakeDepth1Tree:
    def test_basic_structure(self):
        tree = _make_depth1_tree(Fraction(1), Fraction(1, 2), 5)
        assert tree.sqrt_depth == 1
        val = evaluate(tree, dps=30)
        expected = 1.0 + 0.5 * math.sqrt(5)
        assert abs(float(val) - expected) < 1e-20

    def test_zero_a_simplifies(self):
        tree = _make_depth1_tree(Fraction(0), Fraction(1), 2)
        assert tree.sqrt_depth == 1
        val = evaluate(tree, dps=30)
        assert abs(float(val) - math.sqrt(2)) < 1e-20

    def test_golden_ratio_form(self):
        tree = _make_depth1_tree(Fraction(1, 4), Fraction(1, 4), 5)
        val = evaluate(tree, dps=30)
        expected = 0.25 + 0.25 * math.sqrt(5)
        assert abs(float(val) - expected) < 1e-20


class TestMakeNestedTree:
    def test_basic(self):
        inner = _make_depth1_tree(Fraction(1), Fraction(1), 2)
        tree = _make_nested_tree(Fraction(0), Fraction(1), inner)
        assert tree.sqrt_depth == 2
        expected = math.sqrt(1 + math.sqrt(2))
        val = evaluate(tree, dps=30)
        assert abs(float(val) - expected) < 1e-15

    def test_with_coefficients(self):
        inner = _make_depth1_tree(Fraction(3), Fraction(1, 2), 5)
        tree = _make_nested_tree(Fraction(1, 3), Fraction(1, 4), inner)
        assert tree.sqrt_depth == 2
        val = evaluate(tree, dps=30)
        assert val is not None


class TestMakeCorrectionTree:
    def test_adds_surd(self):
        base = _make_depth1_tree(Fraction(1, 2), Fraction(1, 3), 2)
        tree = _make_correction_tree(base, Fraction(1, 5), 3)
        assert tree.sqrt_depth == 1
        val = evaluate(tree, dps=30)
        expected = 0.5 + math.sqrt(2) / 3.0 + math.sqrt(3) / 5.0
        assert abs(float(val) - expected) < 1e-15


# ── search result format ─────────────────────────────────────────────


class TestFieldSearchFormat:
    def test_return_type(self):
        target = compute_target(7, dps=30)
        res = field_search(
            target, 7, max_depth=1, max_height=6, max_radicand=10,
            beam_width=100, dps=30,
        )
        assert isinstance(res, dict)
        for depth, entries in res.items():
            assert isinstance(depth, int)
            assert isinstance(entries, list)
            for err, expr in entries:
                assert isinstance(err, float)
                assert isinstance(expr, ExprNode)

    def test_depths_present(self):
        target = compute_target(7, dps=30)
        res = field_search(
            target, 7, max_depth=2, max_height=6, max_radicand=10,
            beam_width=100, dps=30,
        )
        assert 0 in res
        assert 1 in res
        assert 2 in res

    def test_sorted_by_error(self):
        target = compute_target(7, dps=30)
        res = field_search(
            target, 7, max_depth=1, max_height=6, max_radicand=10,
            beam_width=100, dps=30,
        )
        for depth, entries in res.items():
            errors = [err for err, _ in entries]
            assert errors == sorted(errors)


# ── search quality ───────────────────────────────────────────────────


class TestFieldSearchQuality:
    def test_depth0_finds_close_rational(self):
        target = compute_target(7, dps=50)
        res = field_search(
            target, 7, max_depth=0, max_height=12, max_radicand=10,
            beam_width=500, dps=50,
        )
        best_err = res[0][0][0]
        assert best_err < 1e-3

    def test_depth1_improves_on_depth0(self):
        target = compute_target(7, dps=50)
        res = field_search(
            target, 7, max_depth=1, max_height=12, max_radicand=20,
            beam_width=500, dps=50,
        )
        err0 = res[0][0][0]
        err1 = res[1][0][0]
        assert err1 <= err0

    def test_depth2_improves_on_depth1(self):
        target = compute_target(7, dps=50)
        res = field_search(
            target, 7, max_depth=2, max_height=10, max_radicand=15,
            beam_width=300, dps=50,
        )
        err1 = res[1][0][0]
        err2 = res[2][0][0]
        assert err2 <= err1

    @pytest.mark.parametrize("n", [7, 11, 13])
    def test_depth1_beats_1e4(self, n):
        """Depth-1 surds should approximate cos(2π/n) to at least 1e-4."""
        target = compute_target(n, dps=50)
        res = field_search(
            target, n, max_depth=1, max_height=15, max_radicand=20,
            beam_width=500, dps=50,
        )
        best_err = res[1][0][0]
        assert best_err < 1e-4

    def test_deterministic(self):
        target = compute_target(7, dps=30)
        kw = dict(max_depth=1, max_height=8, max_radicand=10, beam_width=100, dps=30)
        r1 = field_search(target, 7, **kw)
        r2 = field_search(target, 7, **kw)
        assert len(r1[1]) == len(r2[1])
        for (e1, t1), (e2, t2) in zip(r1[1][:10], r2[1][:10]):
            assert e1 == e2
            assert t1 == t2
