"""Tests for expression canonicalization."""

from fractions import Fraction

from aeas.expr import ExprNode, Op
from aeas.canonicalize import canonicalize


def _c(v) -> ExprNode:
    return ExprNode(Op.CONST, value=Fraction(v))


# ── commutative sorting ────────────────────────────────────────────


class TestCommutativeSort:
    def test_add_sorted(self):
        e = ExprNode(Op.ADD, children=(_c(2), _c(1)))
        c = canonicalize(e)
        # constant-folded: 2 + 1 = 3
        assert c.op == Op.CONST and c.value == Fraction(3)

    def test_add_symbolic_sorted(self):
        x = ExprNode(Op.SQRT, children=(_c(2),))
        y = ExprNode(Op.SQRT, children=(_c(3),))
        e = ExprNode(Op.ADD, children=(y, x))
        c = canonicalize(e)
        # sqrt(2) < sqrt(3) lexicographically
        assert c.children[0].to_str() < c.children[1].to_str()

    def test_mul_sorted(self):
        x = ExprNode(Op.SQRT, children=(_c(5),))
        e = ExprNode(Op.MUL, children=(x, _c(2)))
        c = canonicalize(e)
        assert c.children[0].to_str() <= c.children[1].to_str()


# ── constant folding ───────────────────────────────────────────────


class TestConstantFolding:
    def test_add(self):
        c = canonicalize(ExprNode(Op.ADD, children=(_c(1), _c(2))))
        assert c.op == Op.CONST and c.value == Fraction(3)

    def test_mul(self):
        c = canonicalize(ExprNode(Op.MUL, children=(_c(3), _c(4))))
        assert c.op == Op.CONST and c.value == Fraction(12)

    def test_sub(self):
        c = canonicalize(ExprNode(Op.SUB, children=(_c(5), _c(3))))
        assert c.op == Op.CONST and c.value == Fraction(2)

    def test_div(self):
        c = canonicalize(ExprNode(Op.DIV, children=(_c(1), _c(2))))
        assert c.op == Op.CONST and c.value == Fraction(1, 2)

    def test_div_by_zero_not_folded(self):
        e = ExprNode(Op.DIV, children=(_c(1), _c(0)))
        c = canonicalize(e)
        assert c.op == Op.DIV

    def test_sqrt_perfect_square(self):
        c = canonicalize(ExprNode(Op.SQRT, children=(_c(4),)))
        assert c.op == Op.CONST and c.value == Fraction(2)

    def test_sqrt_fraction_perfect_square(self):
        c = canonicalize(ExprNode(Op.SQRT, children=(_c(Fraction(1, 4)),)))
        assert c.op == Op.CONST and c.value == Fraction(1, 2)

    def test_sqrt_non_perfect_stays_symbolic(self):
        c = canonicalize(ExprNode(Op.SQRT, children=(_c(2),)))
        assert c.op == Op.SQRT


# ── identity simplification ────────────────────────────────────────


class TestIdentities:
    def test_add_zero_left(self):
        x = ExprNode(Op.SQRT, children=(_c(2),))
        e = ExprNode(Op.ADD, children=(_c(0), x))
        assert canonicalize(e) == canonicalize(x)

    def test_add_zero_right(self):
        x = ExprNode(Op.SQRT, children=(_c(2),))
        e = ExprNode(Op.ADD, children=(x, _c(0)))
        assert canonicalize(e) == canonicalize(x)

    def test_sub_zero(self):
        x = _c(7)
        e = ExprNode(Op.SUB, children=(x, _c(0)))
        c = canonicalize(e)
        assert c.op == Op.CONST and c.value == Fraction(7)

    def test_mul_one_left(self):
        x = ExprNode(Op.SQRT, children=(_c(3),))
        e = ExprNode(Op.MUL, children=(_c(1), x))
        assert canonicalize(e).op == Op.SQRT

    def test_mul_one_right(self):
        x = ExprNode(Op.SQRT, children=(_c(3),))
        e = ExprNode(Op.MUL, children=(x, _c(1)))
        assert canonicalize(e).op == Op.SQRT

    def test_mul_zero(self):
        x = ExprNode(Op.SQRT, children=(_c(3),))
        e = ExprNode(Op.MUL, children=(x, _c(0)))
        c = canonicalize(e)
        assert c.op == Op.CONST and c.value == Fraction(0)

    def test_div_by_one(self):
        x = ExprNode(Op.SQRT, children=(_c(5),))
        e = ExprNode(Op.DIV, children=(x, _c(1)))
        assert canonicalize(e).op == Op.SQRT

    def test_sqrt_zero(self):
        c = canonicalize(ExprNode(Op.SQRT, children=(_c(0),)))
        assert c.op == Op.CONST and c.value == Fraction(0)

    def test_sqrt_one(self):
        c = canonicalize(ExprNode(Op.SQRT, children=(_c(1),)))
        assert c.op == Op.CONST and c.value == Fraction(1)


# ── idempotence and hash consistency ───────────────────────────────


class TestCanonicalProperties:
    def test_idempotent(self):
        x = ExprNode(Op.SQRT, children=(_c(2),))
        e = ExprNode(Op.ADD, children=(x, _c(1)))
        c1 = canonicalize(e)
        c2 = canonicalize(c1)
        assert c1 == c2
        assert hash(c1) == hash(c2)

    def test_commutative_hash_equality(self):
        """ADD(1, sqrt(2)) and ADD(sqrt(2), 1) should canonicalize identically."""
        x = ExprNode(Op.SQRT, children=(_c(2),))
        a = ExprNode(Op.ADD, children=(_c(1), x))
        b = ExprNode(Op.ADD, children=(x, _c(1)))
        assert canonicalize(a) == canonicalize(b)
        assert hash(canonicalize(a)) == hash(canonicalize(b))
