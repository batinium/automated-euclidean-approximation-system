"""Immutable expression-tree representation for constructible numbers."""

from __future__ import annotations

from enum import Enum, auto
from fractions import Fraction
from typing import Optional, Tuple


class Op(Enum):
    """Supported operations in the expression tree."""

    CONST = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    SQRT = auto()


_OP_SYMBOL = {Op.ADD: "+", Op.SUB: "-", Op.MUL: "*", Op.DIV: "/"}


class ExprNode:
    """Immutable expression-tree node with memoised structural properties.

    Hashing is purely structural so that two trees with identical shape and
    leaf values always compare equal and share the same hash.
    """

    __slots__ = (
        "op",
        "value",
        "children",
        "_hash",
        "_str",
        "_sqrt_depth",
        "_node_count",
    )

    def __init__(
        self,
        op: Op,
        value: Optional[Fraction] = None,
        children: Tuple["ExprNode", ...] = (),
    ) -> None:
        object.__setattr__(self, "op", op)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "children", tuple(children))
        object.__setattr__(self, "_hash", None)
        object.__setattr__(self, "_str", None)
        object.__setattr__(self, "_sqrt_depth", None)
        object.__setattr__(self, "_node_count", None)

    # ---- immutability ------------------------------------------------

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("ExprNode is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("ExprNode is immutable")

    # ---- cached structural metrics -----------------------------------

    @property
    def sqrt_depth(self) -> int:
        """Maximum nesting level of SQRT operations."""
        if self._sqrt_depth is not None:
            return self._sqrt_depth
        if self.op == Op.CONST:
            d = 0
        elif self.op == Op.SQRT:
            d = self.children[0].sqrt_depth + 1
        else:
            d = max(c.sqrt_depth for c in self.children)
        object.__setattr__(self, "_sqrt_depth", d)
        return d

    @property
    def node_count(self) -> int:
        """Total number of nodes in the tree."""
        if self._node_count is not None:
            return self._node_count
        n = 1 + sum(c.node_count for c in self.children)
        object.__setattr__(self, "_node_count", n)
        return n

    # ---- hashing / equality ------------------------------------------

    def __hash__(self) -> int:
        if self._hash is not None:
            return self._hash
        if self.op == Op.CONST:
            h = hash((Op.CONST, self.value))
        else:
            h = hash((self.op, self.children))
        object.__setattr__(self, "_hash", h)
        return h

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExprNode):
            return NotImplemented
        if self is other:
            return True
        if self.op != other.op:
            return False
        if self.op == Op.CONST:
            return self.value == other.value
        return self.children == other.children

    # ---- human-readable string ---------------------------------------

    def to_str(self) -> str:
        """Deterministic, parenthesised infix representation."""
        if self._str is not None:
            return self._str
        s = self._build_str()
        object.__setattr__(self, "_str", s)
        return s

    def _build_str(self) -> str:
        if self.op == Op.CONST:
            v = self.value
            if v.denominator == 1:
                return str(v.numerator)
            return f"({v.numerator}/{v.denominator})"
        if self.op == Op.SQRT:
            return f"sqrt({self.children[0].to_str()})"
        sym = _OP_SYMBOL[self.op]
        return f"({self.children[0].to_str()} {sym} {self.children[1].to_str()})"

    def __repr__(self) -> str:
        return f"Expr({self.to_str()})"
