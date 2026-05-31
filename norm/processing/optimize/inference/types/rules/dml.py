from __future__ import annotations

from sqlglot import exp

from norm.processing.optimize.inference.ast_helpers import (
    contains_node,
    expression_index_containing,
)
from norm.processing.optimize.inference.types.domain import (
    PlaceholderTypeContext,
    Priority,
    constraint,
    known_type,
)


def insert_tuple_rule(ctx: PlaceholderTypeContext):
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
    return constraint(known_type(dtype), "insert_values", Priority.DML, terminal=True)


def update_rule(ctx: PlaceholderTypeContext):
    if not isinstance(ctx.parent, exp.EQ) or not isinstance(
        ctx.parent.parent, exp.Update
    ):
        return []
    if not contains_node(ctx.parent.expression, ctx.placeholder):
        return []

    tuple_dtype = update_tuple_assignment_type(ctx)
    if tuple_dtype:
        return constraint(
            tuple_dtype,
            "update_assignment",
            Priority.DML,
            terminal=True,
        )

    return constraint(
        ctx.type_of(ctx.parent.this),
        "update_assignment",
        Priority.DML,
        terminal=True,
    )


def update_tuple_assignment_type(ctx: PlaceholderTypeContext) -> exp.DataType | None:
    target = ctx.parent.this
    source = ctx.parent.expression

    if not isinstance(target, exp.Tuple) or not isinstance(source, exp.Tuple):
        return None

    if len(target.expressions) != len(source.expressions):
        return None

    value_index = expression_index_containing(source.expressions, ctx.placeholder)
    if value_index is None or value_index >= len(target.expressions):
        return None

    return ctx.type_of(target.expressions[value_index])
