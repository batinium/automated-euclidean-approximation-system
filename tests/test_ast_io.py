from __future__ import annotations

from fractions import Fraction

import pytest

from aeas.ast_io import (
    AstValidationError,
    ast_to_expr,
    canonicalize_ast,
    expr_to_ast,
)
from aeas.canonicalize import canonicalize
from aeas.evaluate import evaluate
from aeas.expr import ExprNode, Op
from aeas.schema_validation import validate_instance


def c(raw: str | int) -> ExprNode:
    return ExprNode(Op.CONST, value=Fraction(raw))


EXPRS = [
    c(0),
    c(1),
    c(-1),
    c("1/2"),
    c("-3/7"),
    ExprNode(Op.ADD, children=(c("1/2"), c("2/3"))),
    ExprNode(Op.SUB, children=(c(0), c("5/8"))),
    ExprNode(Op.MUL, children=(c("-2/3"), c("9/10"))),
    ExprNode(Op.DIV, children=(c(1), c(7))),
    ExprNode(Op.SQRT, children=(c(2),)),
    ExprNode(Op.SQRT, children=(ExprNode(Op.ADD, children=(c(2), c(3))),)),
    ExprNode(
        Op.ADD,
        children=(c("1/2"), ExprNode(Op.SQRT, children=(c(7),))),
    ),
    ExprNode(
        Op.SUB,
        children=(ExprNode(Op.SQRT, children=(c(11),)), c("3/4")),
    ),
    ExprNode(
        Op.MUL,
        children=(c("2/5"), ExprNode(Op.SQRT, children=(c(13),))),
    ),
    ExprNode(
        Op.DIV,
        children=(ExprNode(Op.SQRT, children=(c(17),)), c(3)),
    ),
    ExprNode(
        Op.SQRT,
        children=(
            ExprNode(
                Op.ADD,
                children=(c(3), ExprNode(Op.SQRT, children=(c(5),))),
            ),
        ),
    ),
    ExprNode(
        Op.ADD,
        children=(
            ExprNode(Op.SQRT, children=(c(2),)),
            ExprNode(Op.SQRT, children=(c(3),)),
        ),
    ),
    ExprNode(
        Op.DIV,
        children=(
            ExprNode(
                Op.ADD,
                children=(c(1), ExprNode(Op.SQRT, children=(c(2),))),
            ),
            c(2),
        ),
    ),
    ExprNode(
        Op.SUB,
        children=(
            c(0),
            ExprNode(
                Op.SQRT,
                children=(
                    ExprNode(Op.ADD, children=(c(3), c("1/2"))),
                ),
            ),
        ),
    ),
    ExprNode(
        Op.MUL,
        children=(
            ExprNode(Op.DIV, children=(c(1), c(2))),
            ExprNode(
                Op.SQRT,
                children=(
                    ExprNode(
                        Op.ADD,
                        children=(
                            c(3),
                            ExprNode(Op.SQRT, children=(c(7),)),
                        ),
                    ),
                ),
            ),
        ),
    ),
]


@pytest.mark.parametrize("expr", EXPRS)
def test_expr_to_ast_round_trip(expr: ExprNode) -> None:
    ast = expr_to_ast(expr)
    validate_instance(ast, "ast.schema.json")
    rebuilt = ast_to_expr(ast)

    assert rebuilt == expr


def test_ast_to_expr_handles_wire_unary_ops() -> None:
    asts = [
        {"op": "NEG", "args": [{"op": "CONST", "value": "1/2"}]},
        {"op": "INV", "args": [{"op": "CONST", "value": "7/3"}]},
        {
            "op": "NEG",
            "args": [
                {
                    "op": "SQRT",
                    "args": [{"op": "CONST", "value": "2/1"}],
                }
            ],
        },
    ]

    for ast in asts:
        expr = ast_to_expr(ast)
        out = expr_to_ast(expr)
        validate_instance(out, "ast.schema.json")
        assert canonicalize(ast_to_expr(out)) == canonicalize(expr)


def test_canonicalize_ast_round_trips_through_core_canonicalizer() -> None:
    ast = {
        "op": "ADD",
        "args": [
            {"op": "CONST", "value": "0/1"},
            {
                "op": "NEG",
                "args": [{"op": "CONST", "value": "2/3"}],
            },
        ],
    }

    assert canonicalize_ast(ast) == {"op": "CONST", "value": "-2/3"}


def test_round_trip_preserves_numeric_values() -> None:
    for expr in EXPRS:
        rebuilt = ast_to_expr(expr_to_ast(expr))
        assert evaluate(rebuilt, 80) == evaluate(expr, 80)


@pytest.mark.parametrize(
    "bad_ast",
    [
        {"op": "CONST", "value": "1"},
        {"op": "CONST", "value": "1/-2"},
        {"op": "SQRT", "args": []},
        {"op": "ADD", "args": [{"op": "CONST", "value": "1/1"}]},
        {"op": "POW", "args": [{"op": "CONST", "value": "1/1"}]},
        {"op": "CONST", "value": "1/2", "extra": True},
    ],
)
def test_malformed_ast_raises(bad_ast: dict) -> None:
    with pytest.raises(AstValidationError):
        ast_to_expr(bad_ast)


def test_expr_to_ast_rejects_non_expr() -> None:
    with pytest.raises(AstValidationError):
        expr_to_ast({"op": "CONST", "value": "1/1"})  # type: ignore[arg-type]
