from __future__ import annotations

from sqlglot import exp

from norm.processing.optimize.inference.ast_helpers import (
    contains_node,
    in_values,
    is_direct_placeholder_context,
    is_placeholder_wrapped_by_transparent_expr,
)
from norm.processing.optimize.inference.types.domain import (
    PlaceholderTypeContext,
    Priority,
    cast_target_type,
    constraint,
    data_type,
    merged_type,
)


def cast_rule(ctx: PlaceholderTypeContext):
    parent = ctx.parent
    if not isinstance(parent, exp.Cast):
        return []
    if not is_placeholder_wrapped_by_transparent_expr(parent.this, ctx.placeholder):
        return []
    return constraint(
        cast_target_type(parent),
        "cast",
        Priority.STRUCTURAL,
        terminal=True,
    )


def between_rule(ctx: PlaceholderTypeContext):
    if contains_node(ctx.parent.this, ctx.placeholder):
        dtype = merged_type(
            [
                ctx.child_type("low"),
                ctx.child_type("high"),
            ]
        )
    else:
        dtype = ctx.type_of(ctx.parent.this)
    return constraint(dtype, "between", Priority.COMPARISON, terminal=True)


def in_rule(ctx: PlaceholderTypeContext):
    if contains_node(ctx.parent.this, ctx.placeholder):
        dtype = merged_type(ctx.type_of(expr) for expr in in_values(ctx.parent))
    else:
        dtype = ctx.type_of(ctx.parent.this)
    return constraint(dtype, "in", Priority.COMPARISON, terminal=True)


def is_rule(ctx: PlaceholderTypeContext):
    expression = ctx.parent.args.get("expression")
    if isinstance(expression, exp.Boolean) and contains_node(
        ctx.parent.this, ctx.placeholder
    ):
        return constraint(
            data_type(exp.DType.BOOLEAN),
            "is_boolean",
            Priority.COMPARISON,
            terminal=True,
        )
    return []


def logical_rule(ctx: PlaceholderTypeContext):
    if is_direct_placeholder_context(ctx.parent.this, ctx.current, ctx.placeholder):
        return constraint(
            data_type(exp.DType.BOOLEAN),
            "logical",
            Priority.SOFT,
            terminal=True,
        )

    if is_direct_placeholder_context(
        ctx.parent.expression,
        ctx.current,
        ctx.placeholder,
    ):
        return constraint(
            data_type(exp.DType.BOOLEAN),
            "logical",
            Priority.SOFT,
            terminal=True,
        )

    return []


def not_rule(ctx: PlaceholderTypeContext):
    if is_direct_placeholder_context(ctx.parent.this, ctx.current, ctx.placeholder):
        return constraint(
            data_type(exp.DType.BOOLEAN),
            "not",
            Priority.SOFT,
            terminal=True,
        )
    return []


def predicate_container_rule(ctx: PlaceholderTypeContext):
    if is_direct_placeholder_context(ctx.parent.this, ctx.current, ctx.placeholder):
        return constraint(
            data_type(exp.DType.BOOLEAN),
            "predicate",
            Priority.SOFT,
            terminal=True,
        )
    return []
