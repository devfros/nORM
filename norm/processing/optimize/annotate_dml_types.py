from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlglot import Dialects, Schema, exp
from sqlglot.schema import ensure_schema

from .annotate_types import type_annotator
from .relation_nodes import ordered_physical_tables, tables_from_relation

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .custom_annotator import CustomTypeAnnotator


DML = exp.Update | exp.Delete | exp.Insert
# EXPECTED_VALUE = exp.Parameter | exp.Placeholder | exp.Null


@dataclass(frozen=True)
class SourceIndex:
    schema: Schema
    tables: tuple[exp.Table, ...]
    target: exp.Table | None = None

    @property
    def sources(self) -> dict[str, exp.Table]:
        result: dict[str, exp.Table] = {}
        for table in self.tables:
            for name in _table_names(table):
                result[name] = table
        return result

    def column_type(
        self, column: exp.Column, preferred: exp.Table | None = None
    ) -> exp.DataType:
        if column.table:
            table = self.sources.get(column.table)
            return self._column_type(table, column)

        if preferred:
            preferred_type = self._column_type(preferred, column)
            if not _is_unknown(preferred_type):
                return preferred_type

        matches = [
            dtype
            for table in self.tables
            if not _is_unknown(dtype := self._column_type(table, column))
        ]

        return matches[0] if len(matches) == 1 else exp.DType.UNKNOWN.into_expr()

    def _column_type(
        self, table: exp.Table | None, column: exp.Column | exp.Identifier
    ) -> exp.DataType:
        if table is None:
            return exp.DType.UNKNOWN.into_expr()
        return self.schema.get_column_type(table, column)

    def target_column_type(self, column: exp.Identifier) -> exp.DataType:
        return self._column_type(self.target, column)


def annotate_dml_types(
    expression: exp.Expr, schema: Schema, dialect: Dialects
) -> exp.Expr:
    schema = ensure_schema(schema, dialect=dialect)
    annotator = type_annotator(schema, dialect)
    statements = list(_dml_statements(expression))

    if not statements:
        return expression

    for statement in statements:
        index = SourceIndex(
            schema=schema,
            tables=tuple(ordered_physical_tables(statement)),
            target=_target_table(statement),
        )
        _annotate_statement(statement, index, annotator)

    type_annotator(schema, dialect).annotate_unknowns(expression)
    return expression


def _dml_statements(expression: exp.Expr) -> Iterable[DML]:
    seen: set[int] = set()

    for statement in (
        expression,
        *expression.find_all(exp.Update, exp.Delete, exp.Insert),
    ):
        if (
            isinstance(statement, (exp.Update, exp.Delete, exp.Insert))
            and id(statement) not in seen
        ):
            seen.add(id(statement))
            yield statement


def _annotate_statement(
    statement: DML, index: SourceIndex, annotator: CustomTypeAnnotator
) -> None:
    _annotate_columns(statement, index, annotator)
    _annotate_assignments(statement, index, annotator)
    _annotate_insert(statement, index, annotator)


def _annotate_columns(
    statement: DML, index: SourceIndex, annotator: CustomTypeAnnotator
) -> None:
    for column in statement.find_all(exp.Column):
        dtype = index.column_type(column)
        if not _is_unknown(dtype):
            annotator.set_type(column, dtype)


def _annotate_assignments(
    statement: DML, index: SourceIndex, annotator: CustomTypeAnnotator
) -> None:
    if not isinstance(statement, exp.Update) or index.target is None:
        return

    for assignment in statement.expressions:
        if not isinstance(assignment, exp.EQ) or not isinstance(
            assignment.this, exp.Column
        ):
            continue

        dtype = index.column_type(assignment.this, preferred=index.target)
        if _is_unknown(dtype):
            continue

        annotator.set_type(assignment.this, dtype)
        _annotate_expected_value(assignment.expression, dtype, annotator)


def _annotate_insert(
    statement: DML, index: SourceIndex, annotator: CustomTypeAnnotator
) -> None:
    if not isinstance(statement, exp.Insert) or index.target is None:
        return

    target_columns = _insert_target_columns(statement)
    if not target_columns:
        return

    target_types = [index.target_column_type(column) for column in target_columns]

    for column, dtype in zip(target_columns, target_types, strict=True):
        if not _is_unknown(dtype):
            annotator.set_type(column, dtype)

    source = statement.expression
    if isinstance(source, exp.Values):
        for tuple_ in source.expressions:
            if isinstance(tuple_, exp.Tuple):
                _annotate_positioned_values(tuple_.expressions, target_types, annotator)
    elif isinstance(source, exp.Select):
        _annotate_positioned_values(source.expressions, target_types, annotator)


def _annotate_positioned_values(
    values: list[exp.Expr],
    target_types: list[exp.DataType],
    annotator: CustomTypeAnnotator,
) -> None:
    for value, dtype in zip(values, target_types, strict=False):
        if not _is_unknown(dtype):
            _annotate_expected_value(value, dtype, annotator)


def _annotate_expected_value(
    value: exp.Expr, dtype: exp.DataType, annotator: CustomTypeAnnotator
) -> None:
    if _is_untyped_or_unknown(value):
        annotator.set_type(value, dtype)


def _insert_target_columns(statement: exp.Insert) -> list[exp.Identifier]:
    target = statement.this
    if not isinstance(target, exp.Schema):
        return []
    return [
        column for column in target.expressions if isinstance(column, exp.Identifier)
    ]


def _target_table(statement: DML) -> exp.Table | None:
    tables = tables_from_relation(statement.this)
    return tables[0] if tables else None


def _table_names(table: exp.Table) -> Iterable[str]:
    if table.alias:
        yield table.alias
    if table.name:
        yield table.name


def _is_unknown(dtype: exp.DataType) -> bool:
    return dtype.is_type(exp.DType.UNKNOWN)


def _is_untyped_or_unknown(expression: exp.Expr) -> bool:
    return expression.type is None or _is_unknown(expression.type)
