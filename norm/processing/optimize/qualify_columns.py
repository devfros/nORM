from __future__ import annotations

from sqlglot import Dialects, Schema, exp
from sqlglot.errors import OptimizeError
from sqlglot.optimizer.qualify_columns import qualify_columns as sqlglot_qualify_columns

from .errors import raise_norm_optimize_error
from .relation_nodes import (
    cte_alias_names,
    table_identifier_names,
    tables_for_returning_shadow,
)


def qualify_columns(
    expression: exp.Expr,
    schema: dict[str, object] | Schema,
    dialect: Dialects | None = None,
) -> exp.Expr:
    try:
        optimized = sqlglot_qualify_columns(
            expression,
            schema=schema,
            dialect=dialect,
            expand_alias_refs=False,
            allow_partial_qualification=True,
        )
    except OptimizeError as err:
        raise_norm_optimize_error(err, expression)

    # HACK: sqlglot does not qualify columns  for `RETURNING`
    returning = expression.args.get("returning")
    if isinstance(returning, exp.Returning):
        projections = returning.expressions or []

        shadow = _shadow_select_for_returning(optimized, list(projections))
        if shadow:
            qualified = qualify_columns(
                shadow,
                schema=schema,
                dialect=dialect,
            )
            returning.set("expressions", qualified.expressions)

    return optimized


def _shadow_select_for_returning(
    stmt: exp.Expr,
    projections: list[exp.Expr],
) -> exp.Select | None:
    tables = tables_for_returning_shadow(stmt, projections)
    if not tables:
        return None

    first, *rest = tables
    shadow = exp.Select(
        expressions=projections,
        from_=exp.From(this=first),
        joins=[exp.Join(this=t) for t in rest],
    )
    with_clause = stmt.args.get("with_")
    if with_clause:
        cte_names = cte_alias_names(stmt)
        if any(table_identifier_names(table) & cte_names for table in tables):
            shadow.set("with_", with_clause.copy())
    return shadow
