"""Tests for expression-tree construction and structural properties."""

import pytest
from fractions import Fraction

from aeas.expr import ExprNode, Op


def _c(v) -> ExprNode:
    return ExprNode(Op.CONST, value=Fraction(v))


# ── sqrt_depth ──────────────────────────────────────────────────────


class TestSqrtDepth:
    def test_const(self):
        assert _c(1).sqrt_depth == 0

    def test_binary(self):
        e = ExprNode(Op.ADD, children=(_c(1), _c(2)))
        assert e.sqrt_depth == 0

    def test_single_sqrt(self):
        assert ExprNode(Op.SQRT, children=(_c(2),)).sqrt_depth == 1

    def test_nested_sqrt(self):
        s1 = ExprNode(Op.SQRT, children=(_c(2),))
        s2 = ExprNode(Op.SQRT, children=(s1,))
        assert s2.sqrt_depth == 2

    def test_mixed(self):
        s = ExprNode(Op.SQRT, children=(_c(3),))
        e = ExprNode(Op.ADD, children=(s, _c(1)))
        assert e.sqrt_depth == 1


# ── node_count ──────────────────────────────────────────────────────


class TestNodeCount:
    def test_const(self):
        assert _c(0).node_count == 1

    def test_binary(self):
        e = ExprNode(Op.MUL, children=(_c(2), _c(3)))
        assert e.node_count == 3

    def test_nested(self):
        add = ExprNode(Op.ADD, children=(_c(1), _c(2)))
        sq = ExprNode(Op.SQRT, children=(add,))
        assert sq.node_count == 4


# ── hashing / equality ─────────────────────────────────────────────


class TestHashing:
    def test_identical_structure_same_hash(self):
        e1 = ExprNode(Op.ADD, children=(_c(1), _c(2)))
        e2 = ExprNode(Op.ADD, children=(_c(1), _c(2)))
        assert hash(e1) == hash(e2)
        assert e1 == e2

    def test_different_op_differ(self):
        e1 = ExprNode(Op.ADD, children=(_c(1), _c(2)))
        e2 = ExprNode(Op.SUB, children=(_c(1), _c(2)))
        assert e1 != e2

    def test_different_value_differ(self):
        assert _c(1) != _c(2)

    def test_set_dedup(self):
        e1 = ExprNode(Op.ADD, children=(_c(1), _c(2)))
        e2 = ExprNode(Op.ADD, children=(_c(1), _c(2)))
        s = {e1, e2}
        assert len(s) == 1

    def test_not_equal_to_other_type(self):
        assert _c(1).__eq__("foo") is NotImplemented


# ── immutability ────────────────────────────────────────────────────


def test_immutability():
    e = _c(1)
    with pytest.raises(AttributeError):
        e.op = Op.ADD


# ── string representation ──────────────────────────────────────────


class TestToStr:
    def test_integer(self):
        assert _c(3).to_str() == "3"

    def test_negative(self):
        assert _c(-1).to_str() == "-1"

    def test_fraction(self):
        assert _c(Fraction(1, 2)).to_str() == "(1/2)"

    def test_binary(self):
        e = ExprNode(Op.ADD, children=(_c(1), _c(2)))
        assert e.to_str() == "(1 + 2)"

    def test_sqrt(self):
        e = ExprNode(Op.SQRT, children=(_c(5),))
        assert e.to_str() == "sqrt(5)"

    def test_complex_expr(self):
        inner = ExprNode(Op.SQRT, children=(_c(5),))
        num = ExprNode(Op.ADD, children=(_c(1), inner))
        e = ExprNode(Op.DIV, children=(num, _c(4)))
        assert e.to_str() == "((1 + sqrt(5)) / 4)"
