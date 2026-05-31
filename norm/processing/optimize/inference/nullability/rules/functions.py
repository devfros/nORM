from __future__ import annotations

from norm.processing.optimize.inference.ast_helpers import (
    contains_node,
    direct_child_expressions,
)
from norm.processing.optimize.inference.nullability.domain import (
    PlaceholderNullabilityContext,
    Priority,
    constraint,
)


def nullable_function_rule(ctx: PlaceholderNullabilityContext):
    if any(
        contains_node(expr, ctx.placeholder)
        for expr in direct_child_expressions(ctx.parent)
    ):
        return constraint(
            nullable=True,
            source="null_function",
            priority=Priority.FUNCTION,
            terminal=True,
        )
    return []
