from __future__ import annotations

from sqlglot import exp

from norm.processing.optimize.inference.ast_helpers import contains_node
from norm.processing.optimize.inference.nullability.domain import (
    PlaceholderNullabilityContext,
    Priority,
    constraint,
    merged_nullability,
)


def if_rule(ctx: PlaceholderNullabilityContext):
    true_value = ctx.parent.args.get("true")
    false_value = ctx.parent.args.get("false")

    if isinstance(true_value, exp.Expr) and contains_node(true_value, ctx.placeholder):
        return constraint(
            ctx.nullability_of(false_value)
            if isinstance(false_value, exp.Expr)
            else None,
            source="case_result",
            priority=Priority.FUNCTION,
            terminal=True,
        )

    if isinstance(false_value, exp.Expr) and contains_node(
        false_value, ctx.placeholder
    ):
        return constraint(
            ctx.nullability_of(true_value)
            if isinstance(true_value, exp.Expr)
            else None,
            source="case_result",
            priority=Priority.FUNCTION,
            terminal=True,
        )

    return []


def case_rule(ctx: PlaceholderNullabilityContext):
    ifs = [
        item for item in ctx.parent.args.get("ifs") or [] if isinstance(item, exp.If)
    ]
    default = ctx.parent.args.get("default")

    if isinstance(default, exp.Expr) and contains_node(default, ctx.placeholder):
        nullable = merged_nullability(if_result_nullability(item, ctx) for item in ifs)
        return constraint(
            nullable,
            source="case_result",
            priority=Priority.FUNCTION,
            terminal=True,
        )

    for item in ifs:
        if placeholder_in_if_result(item, ctx.placeholder):
            nullable = merged_nullability(
                [
                    ctx.nullability_of(default)
                    if isinstance(default, exp.Expr)
                    else None,
                    *(
                        if_result_nullability(other, ctx)
                        for other in ifs
                        if other is not item
                    ),
                ]
            )
            return constraint(
                nullable,
                source="case_result",
                priority=Priority.FUNCTION,
                terminal=True,
            )

    return []


def if_result_nullability(
    if_: exp.If,
    ctx: PlaceholderNullabilityContext,
) -> bool | None:
    true_value = if_.args.get("true")
    false_value = if_.args.get("false")
    return merged_nullability(
        [
            ctx.nullability_of(true_value)
            if isinstance(true_value, exp.Expr)
            else None,
            ctx.nullability_of(false_value)
            if isinstance(false_value, exp.Expr)
            else None,
        ]
    )


def placeholder_in_if_result(if_: exp.If, placeholder: exp.Placeholder) -> bool:
    for arg_key in ("true", "false"):
        value = if_.args.get(arg_key)
        if isinstance(value, exp.Expr) and contains_node(value, placeholder):
            return True
    return False
