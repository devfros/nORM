from __future__ import annotations

from sqlglot import exp
from sqlglot.optimizer.scope import Scope


def unwrap_expression(expression: exp.Expr) -> exp.Expr:
    if isinstance(expression, exp.Lateral):
        return unwrap_expression(expression.this)

    if isinstance(expression, exp.Subquery):
        return unwrap_expression(expression.this)

    return expression


def statement_projections(statement: exp.Expr) -> list[exp.Expr]:
    statement = unwrap_expression(statement)

    if isinstance(statement, exp.Select):
        return list(statement.expressions or [])

    returning = statement.args.get("returning")
    if isinstance(returning, exp.Returning):
        return list(returning.expressions or [])

    return []


def scope_projections(scope: Scope) -> list[exp.Expr]:
    return statement_projections(scope.expression)


def find_cte(query: exp.Expr, alias: str) -> exp.CTE | None:
    if not alias:
        return None

    for with_clause in query.find_all(exp.With):
        for cte in with_clause.expressions:
            if isinstance(cte, exp.CTE) and _same_identifier(cte.alias_or_name, alias):
                return cte

    return None


def cte_in_scope(scope: Scope, alias: str) -> exp.CTE | None:
    if not alias:
        return None

    for cte in scope.ctes or []:
        if isinstance(cte, exp.CTE) and _same_identifier(cte.alias_or_name, alias):
            return cte

    return None


def cte_for_table(query: exp.Expr, table: exp.Table) -> exp.CTE | None:
    if table_expression(table) is not None:
        return None

    return find_cte(query, table.name)


def cte_for_table_in_scope(scope: Scope, table: exp.Table) -> exp.CTE | None:
    if table_expression(table) is not None:
        return None

    return cte_in_scope(scope, table.name)


def table_expression(table: exp.Table) -> exp.Expr | None:
    expression = table.this
    if isinstance(expression, exp.Expr) and not isinstance(expression, exp.Identifier):
        return expression

    return None


def projection_output_names(projection: exp.Expr) -> list[str]:
    names = [projection.alias_or_name]
    default_name = _default_projection_name(projection)
    if default_name:
        names.insert(0, default_name)

    return [name for name in names if name]


def _default_projection_name(expression: exp.Expr) -> str | None:
    if isinstance(expression, exp.Alias):
        return _default_projection_name(expression.this)

    if isinstance(expression, exp.Column):
        return expression.name

    if isinstance(expression, exp.Count):
        return "count"

    if isinstance(expression, exp.Anonymous):
        return str(expression.name).lower()

    if isinstance(expression, exp.WithinGroup):
        return _default_projection_name(expression.this)

    if isinstance(expression, exp.PercentileDisc):
        return "percentile_disc"

    return expression.name or None


def _same_identifier(left: str, right: str) -> bool:
    return left == right or left.lower() == right.lower()
