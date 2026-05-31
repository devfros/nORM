from __future__ import annotations

from sqlglot import exp

RelationNode = exp.Expr | list[exp.Expr] | None


def query_relation_nodes(query: exp.Expr) -> list[RelationNode]:
    result: list[RelationNode] = []

    if isinstance(query, exp.Select):
        result = [query.args.get("from_"), query.args.get("joins")]
    elif isinstance(query, exp.Insert):
        result = [query.this]
    elif isinstance(query, exp.Update):
        result = [query.this, query.args.get("from_"), query.args.get("joins")]
    elif isinstance(query, exp.Delete):
        result = [query.this, query.args.get("using"), query.args.get("joins")]

    return result


def tables_from_relation(relation: RelationNode) -> list[exp.Table]:
    if relation is None:
        return []

    if isinstance(relation, list):
        out: list[exp.Table] = []
        for item in relation:
            out.extend(tables_from_relation(item))
        return out

    if isinstance(relation, exp.Table):
        out = [relation]
        out.extend(tables_from_relation(relation.args.get("joins")))
        return out

    if isinstance(relation, exp.Join):
        return tables_from_relation(relation.this)

    if isinstance(relation, exp.From):
        out = tables_from_relation(relation.this)
        out.extend(tables_from_relation(relation.expressions))
        return out

    if isinstance(relation, exp.Schema):
        return tables_from_relation(relation.this)

    return []


def ordered_physical_tables(query: exp.Expr) -> list[exp.Table]:
    tables: list[exp.Table] = []
    for relation in query_relation_nodes(query):
        tables.extend(tables_from_relation(relation))
    return tables


DML = exp.Update | exp.Delete | exp.Insert


def dml_target_table(statement: DML) -> exp.Table | None:
    tables = tables_from_relation(statement.this)
    return tables[0] if tables else None


def cte_alias_names(statement: exp.Expr) -> set[str]:
    with_ = statement.args.get("with_")
    if not isinstance(with_, exp.With):
        return set()

    names: set[str] = set()
    for cte in with_.expressions:
        if cte.alias:
            names.add(cte.alias)
    return names


def _star_table_qualifier(star: exp.Star) -> str | None:
    qualifier = star.args.get("table")
    if isinstance(qualifier, exp.Identifier):
        return qualifier.name
    if isinstance(qualifier, str):
        return qualifier
    return None


def table_identifier_names(table: exp.Table) -> set[str]:
    names: set[str] = set()
    if table.name:
        names.add(table.name)
    if table.alias:
        names.add(table.alias)
    if table.db:
        names.add(table.db)
    return names


def _table_matches_qualifier(table: exp.Table, qualifier: str) -> bool:
    return qualifier in table_identifier_names(table)


def tables_for_returning_shadow(
    statement: exp.Expr,
    projections: list[exp.Expr],
) -> list[exp.Table]:
    if not isinstance(statement, DML):
        return ordered_physical_tables(statement)

    stars = [item for item in projections if isinstance(item, exp.Star)]
    if not stars:
        return ordered_physical_tables(statement)

    target = dml_target_table(statement)
    qualifiers = {_star_table_qualifier(star) for star in stars}
    qualifiers.discard(None)

    if not qualifiers:
        return [target.copy()] if target is not None else []

    all_tables = ordered_physical_tables(statement)
    matched = [
        table
        for table in all_tables
        if any(_table_matches_qualifier(table, qualifier) for qualifier in qualifiers)
    ]
    if matched:
        return [table.copy() for table in matched]

    return [target.copy()] if target is not None else []
