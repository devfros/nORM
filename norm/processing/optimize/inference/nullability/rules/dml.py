from __future__ import annotations

from sqlglot import exp

from norm.processing.optimize.inference.ast_helpers import (
    expression_index_containing,
    is_direct_placeholder_context,
)
from norm.processing.optimize.inference.nullability.domain import (
    PlaceholderNullabilityContext,
    Priority,
    constraint,
    nullable_from_type,
)


def insert_tuple_rule(ctx: PlaceholderNullabilityContext):
    if not isinstance(ctx.parent, exp.Tuple):
        return []

    insert = ctx.parent.find_ancestor(exp.Insert)
    if not insert:
        return []

    target = insert.this
    if not isinstance(target, exp.Schema) or not isinstance(target.this, exp.Table):
        return []

    if len(ctx.parent.expressions) != len(target.expressions):
        return []

    value_index = expression_index_containing(ctx.parent.expressions, ctx.placeholder)
    if value_index is None or value_index >= len(target.expressions):
        return []

    target_column = target.expressions[value_index]
    if not isinstance(target_column, exp.Identifier):
        return []

    dtype = ctx.schema.get_column_type(target.this, target_column)
    return constraint(
        nullable_from_type(dtype),
        source="insert_values",
        priority=Priority.DML,
        terminal=True,
    )


def update_rule(ctx: PlaceholderNullabilityContext):
    if not isinstance(ctx.parent, exp.EQ) or not isinstance(
        ctx.parent.parent, exp.Update
    ):
        return []

    tuple_nullable = update_tuple_assignment_nullability(ctx)
    if tuple_nullable is not None:
        return constraint(
            tuple_nullable,
            source="update_assignment",
            priority=Priority.DML,
            terminal=True,
        )

    if not is_direct_placeholder_context(
        ctx.parent.expression,
        ctx.current,
        ctx.placeholder,
        transparent_types=(exp.Cast, exp.Paren),
    ):
        return []

    return constraint(
        ctx.nullability_of(ctx.parent.this),
        source="update_assignment",
        priority=Priority.DML,
        terminal=True,
    )


def update_tuple_assignment_nullability(
    ctx: PlaceholderNullabilityContext,
) -> bool | None:
    target = ctx.parent.this
    source = ctx.parent.expression

    if not isinstance(target, exp.Tuple) or not isinstance(source, exp.Tuple):
        return None

    if len(target.expressions) != len(source.expressions):
        return None

    value_index = expression_index_containing(source.expressions, ctx.placeholder)
    if value_index is None or value_index >= len(target.expressions):
        return None

    return ctx.nullability_of(target.expressions[value_index])
