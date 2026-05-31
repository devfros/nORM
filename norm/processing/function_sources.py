from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlglot import Dialects, exp

from norm.processing.query_sources import table_expression


@dataclass(frozen=True)
class FunctionColumn:
    name: str
    dtype: exp.DType


@dataclass(frozen=True)
class FunctionSource:
    expression: exp.Expr
    columns: tuple[FunctionColumn, ...]


FunctionSourceResolver = Callable[[exp.Expr], FunctionSource | None]


_POSTGRES_ANONYMOUS_FUNCTION_COLUMNS: dict[str, tuple[FunctionColumn, ...]] = {
    "jsonb_array_elements": (FunctionColumn("value", exp.DType.JSONB),),
    "jsonb_each": (
        FunctionColumn("key", exp.DType.TEXT),
        FunctionColumn("value", exp.DType.JSONB),
    ),
}

_POSTGRES_TYPED_FUNCTION_SOURCES: dict[type[exp.Expr], FunctionSourceResolver] = {
    exp.CurrentTimestamp: lambda expression: FunctionSource(
        expression=expression,
        columns=(FunctionColumn("now", exp.DType.TIMESTAMPTZ),),
    ),
}


def expand_function_stars(expression: exp.Expr, dialect: Dialects) -> exp.Expr:
    resolver = _RESOLVERS.get(dialect)
    if resolver is None:
        return expression

    for select in expression.find_all(exp.Select):
        stars = [
            item for item in select.expressions or [] if isinstance(item, exp.Star)
        ]
        if not stars:
            continue

        sources = _select_sources(select)
        if not sources:
            continue

        expanded: list[exp.Expr] = []
        changed = False

        for item in select.expressions or []:
            if not isinstance(item, exp.Star):
                expanded.append(item)
                continue

            replacements = _expand_star(item, sources, resolver)
            if replacements:
                changed = True
                expanded.extend(replacements)
            else:
                expanded.append(item)

        if changed:
            select.set("expressions", expanded)

    return expression


def function_source_columns(
    table: exp.Table,
    dialect: Dialects,
) -> dict[str, exp.DataType]:
    resolver = _RESOLVERS.get(dialect)
    if resolver is None:
        return {}

    source = _function_source(table, resolver)
    if source is None:
        return {}

    alias_names = list(table.alias_column_names or [])
    columns: dict[str, exp.DataType] = {}

    for index, column in enumerate(source.columns):
        name = alias_names[index] if index < len(alias_names) else column.name
        columns[name] = exp.DataType.build(column.dtype)

    if len(alias_names) > len(source.columns):
        columns.setdefault(alias_names[-1], exp.DataType.build(exp.DType.BIGINT))

    return columns


def _expand_star(
    star: exp.Star,
    sources: list[tuple[str | None, exp.Table]],
    resolver: FunctionSourceResolver,
) -> list[exp.Expr]:
    qualifier = star.args.get("table")
    if isinstance(qualifier, exp.Identifier):
        table_name = qualifier.name
    elif isinstance(qualifier, str):
        table_name = qualifier
    else:
        table_name = None

    if table_name:
        matches = [
            source
            for name, source in sources
            if name and _same_identifier(name, table_name)
        ]
    else:
        matches = [source for _, source in sources]

    if len(matches) != 1:
        return []

    function_source = _function_source(matches[0], resolver)
    if function_source is None:
        return []

    return [
        _projection_for_column(function_source, column)
        for column in function_source.columns
    ]


def _projection_for_column(
    source: FunctionSource,
    column: FunctionColumn,
) -> exp.Alias:
    if len(source.columns) == 1:
        value = source.expression
    else:
        value = exp.Column(this=exp.to_identifier(column.name))

    return exp.Alias(
        this=value,
        alias=exp.to_identifier(column.name),
    )


def _function_source(
    table: exp.Table,
    resolver: FunctionSourceResolver,
) -> FunctionSource | None:
    expression = table_expression(table)
    if expression is None:
        return None

    source = resolver(expression)
    if source is not None:
        return source

    return _anonymous_function_source(expression)


def _anonymous_function_source(expression: exp.Expr) -> FunctionSource | None:
    if not isinstance(expression, exp.Anonymous):
        return None

    columns = _POSTGRES_ANONYMOUS_FUNCTION_COLUMNS.get(str(expression.name).lower())
    if not columns:
        return None

    return FunctionSource(expression=expression, columns=columns)


def _postgres_function_source(expression: exp.Expr) -> FunctionSource | None:
    resolver = _POSTGRES_TYPED_FUNCTION_SOURCES.get(type(expression))
    if resolver is not None:
        return resolver(expression)

    return _anonymous_function_source(expression)


def _select_sources(select: exp.Select) -> list[tuple[str | None, exp.Table]]:
    sources: list[tuple[str | None, exp.Table]] = []

    from_ = select.args.get("from_")
    if from_ and isinstance(from_.this, exp.Table):
        sources.append((_table_source_name(from_.this), from_.this))

    for join in select.args.get("joins") or []:
        if isinstance(join.this, exp.Table):
            sources.append((_table_source_name(join.this), join.this))

    return sources


def _table_source_name(table: exp.Table) -> str | None:
    if table.alias:
        return table.alias

    expression = table_expression(table)
    if expression is not None:
        return None

    return table.name or None


def _same_identifier(left: str, right: str) -> bool:
    return left == right or left.lower() == right.lower()


_RESOLVERS: dict[Dialects, FunctionSourceResolver] = {
    Dialects.POSTGRES: _postgres_function_source,
}
