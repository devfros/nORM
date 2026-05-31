from __future__ import annotations

from sqlglot import exp


def contains_node(root: exp.Expr | None, node: exp.Expr) -> bool:
    if root is None:
        return False
    if root is node:
        return True
    return any(item is node for item in root.walk())


def direct_child_expressions(expression: exp.Expr):
    for value in expression.args.values():
        if isinstance(value, exp.Expr):
            yield value
        elif isinstance(value, list):
            yield from (item for item in value if isinstance(item, exp.Expr))


def expression_index_containing(
    expressions: list[exp.Expr],
    target: exp.Expr,
) -> int | None:
    for idx, expression in enumerate(expressions):
        if contains_node(expression, target):
            return idx
    return None


def is_placeholder_wrapped_by_transparent_expr(
    expression: exp.Expr | None,
    placeholder: exp.Placeholder,
    transparent_types: tuple[type[exp.Expr], ...] = (exp.Paren,),
) -> bool:
    if expression is placeholder:
        return True
    if isinstance(expression, transparent_types):
        return is_placeholder_wrapped_by_transparent_expr(
            expression.this,
            placeholder,
            transparent_types=transparent_types,
        )
    return False


def is_direct_placeholder_context(
    expression: exp.Expr | None,
    current: exp.Expr,
    placeholder: exp.Placeholder,
    transparent_types: tuple[type[exp.Expr], ...] = (exp.Paren,),
) -> bool:
    return expression is current and is_placeholder_wrapped_by_transparent_expr(
        current,
        placeholder,
        transparent_types=transparent_types,
    )


def other_binary_side(
    parent: exp.Expr, placeholder: exp.Placeholder
) -> exp.Expr | None:
    left = parent.args.get("this")
    right = parent.args.get("expression")
    if isinstance(left, exp.Expr) and contains_node(left, placeholder):
        return right if isinstance(right, exp.Expr) else None
    return left if isinstance(left, exp.Expr) else None


def in_values(parent: exp.Expr):
    yield from parent.expressions or []
    query = parent.args.get("query")
    if isinstance(query, exp.Expr):
        yield query
