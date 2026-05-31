from __future__ import annotations

from sqlglot import exp

from norm.processing.optimize.inference.ast_helpers import contains_node
from norm.processing.optimize.inference.nullability.domain import (
    PlaceholderNullabilityContext,
    Priority,
    constraint,
)


def is_null_rule(ctx: PlaceholderNullabilityContext):
    expression = ctx.parent.args.get("expression")
    if isinstance(expression, exp.Null) and contains_node(
        ctx.parent.this, ctx.placeholder
    ):
        return constraint(
            nullable=True,
            source="is_null",
            priority=Priority.EXPLICIT,
            terminal=True,
        )
    return []
