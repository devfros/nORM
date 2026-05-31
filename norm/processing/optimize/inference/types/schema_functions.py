from __future__ import annotations

from typing import TYPE_CHECKING

from norm.processing.optimize.inference.ast_helpers import contains_node
from norm.processing.optimize.inference.types.domain import (
    PlaceholderTypeContext,
    Priority,
    constraint,
)
from norm.schemas.function_calls import (
    enclosing_schema_function_call,
    positional_schema_parameter_types,
    resolve_schema_function,
)

if TYPE_CHECKING:
    from sqlglot import exp


def schema_function_argument_types(
    ctx: PlaceholderTypeContext,
) -> dict[int, exp.DataType]:
    db_schema = ctx.db_schema
    if db_schema is None:
        return {}

    catalog_name, function_name, _args = enclosing_schema_function_call(ctx.placeholder)
    if not function_name:
        return {}

    function = resolve_schema_function(
        db_schema,
        function_name,
        catalog_name,
        _args,
    )
    if function is None:
        return {}

    return positional_schema_parameter_types(function)


def schema_function_argument_rule(ctx: PlaceholderTypeContext):
    schema_types = schema_function_argument_types(ctx)
    if not schema_types:
        return []

    _catalog_name, _function_name, call_args = enclosing_schema_function_call(
        ctx.placeholder
    )
    for index, arg in enumerate(call_args):
        if contains_node(arg, ctx.placeholder) and index in schema_types:
            return constraint(
                schema_types[index],
                "schema_function",
                Priority.FUNCTION,
                terminal=True,
            )

    return []
