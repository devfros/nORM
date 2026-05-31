from __future__ import annotations

from sqlglot import exp

from norm.processing.optimize.inference.types.domain import (
    PlaceholderTypeContext,
    Priority,
    TypeConstraint,
)
from norm.processing.optimize.inference.types.rules.builders import (
    same_as_other_binary_side,
    same_as_siblings,
)
from norm.processing.optimize.inference.types.rules.dml import update_rule


def eq_rule(ctx: PlaceholderTypeContext) -> list[TypeConstraint]:
    return update_rule(ctx) or same_as_other_binary_side(
        source="comparison",
        priority=Priority.COMPARISON,
    )(ctx)


COMPARISON_RULES = {
    exp.EQ: eq_rule,
    exp.NEQ: same_as_other_binary_side(
        source="comparison",
        priority=Priority.COMPARISON,
    ),
    exp.GT: same_as_other_binary_side(
        source="comparison",
        priority=Priority.COMPARISON,
    ),
    exp.GTE: same_as_other_binary_side(
        source="comparison",
        priority=Priority.COMPARISON,
    ),
    exp.LT: same_as_other_binary_side(
        source="comparison",
        priority=Priority.COMPARISON,
    ),
    exp.LTE: same_as_other_binary_side(
        source="comparison",
        priority=Priority.COMPARISON,
    ),
    exp.Like: same_as_other_binary_side(
        source="like",
        priority=Priority.COMPARISON,
        fallback=exp.DType.TEXT,
    ),
    exp.ILike: same_as_other_binary_side(
        source="like",
        priority=Priority.COMPARISON,
        fallback=exp.DType.TEXT,
    ),
    exp.Distance: same_as_other_binary_side(
        source="distance",
        priority=Priority.COMPARISON,
    ),
}

ARITHMETIC_RULES = {
    exp.Add: same_as_other_binary_side(
        source="arithmetic",
        priority=Priority.ARITHMETIC,
        fallback=exp.DType.DOUBLE,
    ),
    exp.Sub: same_as_other_binary_side(
        source="arithmetic",
        priority=Priority.ARITHMETIC,
        fallback=exp.DType.DOUBLE,
    ),
    exp.Mul: same_as_other_binary_side(
        source="arithmetic",
        priority=Priority.ARITHMETIC,
        fallback=exp.DType.DOUBLE,
    ),
    exp.Div: same_as_other_binary_side(
        source="arithmetic",
        priority=Priority.ARITHMETIC,
        fallback=exp.DType.DOUBLE,
    ),
    exp.Mod: same_as_other_binary_side(
        source="arithmetic",
        priority=Priority.ARITHMETIC,
        fallback=exp.DType.DOUBLE,
    ),
}

CONCAT_RULES = {
    exp.DPipe: same_as_siblings(
        source="concat",
        priority=Priority.COMPARISON,
        fallback=exp.DType.TEXT,
    ),
}
