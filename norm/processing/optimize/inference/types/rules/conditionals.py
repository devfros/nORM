from __future__ import annotations

from sqlglot import exp

from norm.processing.optimize.inference.ast_helpers import (
    contains_node,
    is_direct_placeholder_context,
)
from norm.processing.optimize.inference.types.domain import (
    PlaceholderTypeContext,
    Priority,
    constraint,
    data_type,
    merged_type,
)


def if_rule(ctx: PlaceholderTypeContext):
    condition = ctx.parent.args.get("this")
    true_value = ctx.parent.args.get("true")
    false_value = ctx.parent.args.get("false")

    if is_direct_placeholder_context(condition, ctx.current, ctx.placeholder):
        return constraint(
            data_type(exp.DType.BOOLEAN),
            "case_condition",
            Priority.SOFT,
            terminal=True,
        )

    if isinstance(true_value, exp.Expr) and contains_node(true_value, ctx.placeholder):
        return constraint(
            ctx.type_of(false_value) if isinstance(false_value, exp.Expr) else None,
            "case_result",
            Priority.FUNCTION,
            terminal=True,
        )

    if isinstance(false_value, exp.Expr) and contains_node(
        false_value, ctx.placeholder
    ):
        return constraint(
            ctx.type_of(true_value) if isinstance(true_value, exp.Expr) else None,
            "case_result",
            Priority.FUNCTION,
            terminal=True,
        )

    return []


def case_rule(ctx: PlaceholderTypeContext):
    ifs = [
        item for item in ctx.parent.args.get("ifs") or [] if isinstance(item, exp.If)
    ]
    default = ctx.parent.args.get("default")

    if isinstance(default, exp.Expr) and contains_node(default, ctx.placeholder):
        dtype = merged_type(if_result_type(item, ctx) for item in ifs)
        return constraint(dtype, "case_result", Priority.FUNCTION, terminal=True)

    for item in ifs:
        if placeholder_in_if_result(item, ctx.placeholder):
            dtype = merged_type(
                [
                    ctx.type_of(default) if isinstance(default, exp.Expr) else None,
                    *(if_result_type(other, ctx) for other in ifs if other is not item),
                ]
            )
            return constraint(dtype, "case_result", Priority.FUNCTION, terminal=True)

    return []


def if_result_type(if_: exp.If, ctx: PlaceholderTypeContext) -> exp.DataType | None:
    true_value = if_.args.get("true")
    false_value = if_.args.get("false")
    return merged_type(
        [
            ctx.type_of(true_value) if isinstance(true_value, exp.Expr) else None,
            ctx.type_of(false_value) if isinstance(false_value, exp.Expr) else None,
        ]
    )


def placeholder_in_if_result(if_: exp.If, placeholder: exp.Placeholder) -> bool:
    for arg_key in ("true", "false"):
        value = if_.args.get(arg_key)
        if isinstance(value, exp.Expr) and contains_node(value, placeholder):
            return True
    return False
