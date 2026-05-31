from __future__ import annotations

from sqlglot import exp

from norm.processing.optimize.inference.ast_helpers import (
    contains_node,
    direct_child_expressions,
)
from norm.processing.optimize.inference.types.domain import (
    PlaceholderTypeContext,
    Priority,
    constraint,
    data_type,
)
from norm.processing.optimize.inference.types.rules.builders import same_as_siblings
from norm.processing.optimize.inference.types.schema_functions import (
    schema_function_argument_rule,
)

TEXT_FUNCTIONS: tuple[type[exp.Func], ...] = (
    exp.Concat,
    exp.Length,
    exp.Lower,
    exp.Trim,
    exp.Upper,
)

NUMERIC_FUNCTIONS: tuple[type[exp.Func], ...] = (
    exp.Abs,
    exp.Ceil,
    exp.Floor,
    exp.Pow,
    exp.Round,
    exp.Sqrt,
)

POSTGRES_FUNCTION_ARG_TYPES: dict[str, dict[int, exp.DType]] = {
    "pg_advisory_lock": {0: exp.DType.BIGINT},
    "pg_advisory_unlock": {0: exp.DType.BIGINT},
}


def function_signature_rule(ctx: PlaceholderTypeContext):
    schema_constraints = schema_function_argument_rule(ctx)
    if schema_constraints:
        return schema_constraints

    parent = ctx.parent

    if isinstance(parent, (exp.Coalesce, exp.Nullif)):
        return same_as_siblings(
            source="function",
            priority=Priority.FUNCTION,
        )(ctx)

    positional = function_positional_types(parent, ctx)
    if positional:
        args = list(direct_child_expressions(parent))
        for idx, arg in enumerate(args):
            if contains_node(arg, ctx.placeholder) and idx in positional:
                return constraint(
                    positional[idx],
                    "function",
                    Priority.FUNCTION,
                    terminal=True,
                )

    if isinstance(parent, TEXT_FUNCTIONS):
        return constraint(
            data_type(exp.DType.TEXT),
            "function",
            Priority.FUNCTION,
            terminal=True,
        )

    if isinstance(parent, NUMERIC_FUNCTIONS):
        return constraint(
            data_type(exp.DType.DECIMAL),
            "function",
            Priority.FUNCTION,
            terminal=True,
        )

    return same_as_siblings(source="function", priority=Priority.FUNCTION)(ctx)


def function_positional_types(
    expression: exp.Expr,
    _ctx: PlaceholderTypeContext,
) -> dict[int, exp.DataType]:
    if isinstance(expression, exp.Anonymous):
        arg_types = POSTGRES_FUNCTION_ARG_TYPES.get(str(expression.name).lower())
        if arg_types:
            return {idx: data_type(dtype) for idx, dtype in arg_types.items()}

    if isinstance(expression, exp.Substring):
        return {
            0: data_type(exp.DType.TEXT),
            1: data_type(exp.DType.INT),
            2: data_type(exp.DType.INT),
        }
    if isinstance(expression, exp.Replace):
        return {
            0: data_type(exp.DType.TEXT),
            1: data_type(exp.DType.TEXT),
            2: data_type(exp.DType.TEXT),
        }
    return {}
