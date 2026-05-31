from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from sqlglot import exp
from sqlglot.expressions import DType
from sqlglot.optimizer.scope import Scope, traverse_scope

from norm.consts import MetaKeys
from norm.errors import NormError, NormErrorCode
from norm.processing.query_sources import (
    cte_for_table,
    scope_projections,
    statement_projections,
    table_expression,
)
from norm.schemas.function_calls import (
    enclosing_schema_function_call,
    resolve_schema_function,
)
from norm.schemas.parsing import (
    DBSchema,
    FieldDefinition,
    FunctionDefinition,
    ModelDefinition,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


_AUTO_ALIAS = re.compile(r"_col_\d+$")


class ReturnFieldResolver:
    def __init__(self, db_schema: DBSchema) -> None:
        self.db_schema = db_schema

    def build_field(self, item: exp.Expr, query: exp.Expr) -> FieldDefinition:
        datatype = self._type_of(item)
        if datatype and not datatype.is_type(DType.UNKNOWN):
            meta_field = self._field_from_datatype_meta(item, datatype)
            if meta_field:
                field = meta_field.model_copy(deep=True)
                field.name = self.output_name(item, meta_field.name)
                return field

        source_field = self._field_for(_projection_source(item), query)
        if source_field:
            field = source_field.model_copy(deep=True)
            field.name = self.output_name(item, source_field.name)
            if datatype and not datatype.is_type(DType.UNKNOWN):
                field.datatype = datatype
            return field

        schema_function = self._schema_function_for_projection(_projection_source(item))
        if schema_function is not None:
            return self._field_from_schema_function(item, schema_function)

        if not datatype or datatype.is_type(DType.UNKNOWN):
            raise NormError(
                code=NormErrorCode.AMBIGUOUS_COLUMN,
                message="Couldn't infer the type of column",
                context={"column": str(item)},
            )

        return FieldDefinition(name=self.output_name(item), datatype=datatype)

    def _field_from_datatype_meta(
        self,
        item: exp.Expr,
        datatype: exp.DataType,
    ) -> FieldDefinition | None:
        source = _projection_source(item)
        table_name = datatype.meta.get(MetaKeys.TABLE_NAME)
        catalog_name = datatype.meta.get(MetaKeys.CATALOG_NAME)
        column_name = _column_name(source)
        if not table_name or not column_name:
            return None

        return self.db_schema.get_field(column_name, table_name, catalog_name)

    def output_name(self, item: exp.Expr, source_name: str | None = None) -> str:
        if isinstance(item, exp.Alias):
            alias = item.alias
            if _is_auto_alias(alias):
                return (
                    _default_projection_name(item.this)
                    or source_name
                    or alias.replace("_col", "column")
                )

            source = _projection_source(item)
            if (
                source_name
                and _column_name(source) == alias
                and source_name.lower() == alias
            ):
                return source_name

            return alias

        return item.alias_or_name.replace("_col", "column")

    def _type_of(self, expression: exp.Expr) -> exp.DataType | None:
        datatype = expression.type
        if datatype and not datatype.is_type(DType.UNKNOWN):
            return datatype

        if isinstance(expression, exp.Alias):
            return self._type_of(expression.this)

        return None

    def _field_for(
        self, expression: exp.Expr, query: exp.Expr
    ) -> FieldDefinition | None:
        if isinstance(expression, exp.Alias):
            return self._field_for(expression.this, query)

        if not isinstance(expression, exp.Column):
            return None

        if expression.table:
            source = self._find_source(expression.table, query)
            if source:
                return self._field_from_source(source, expression.name, query)

            return self.db_schema.get_field(
                expression.name,
                expression.table,
                expression.db or None,
            )

        return self._unique_visible_field(expression.name, query)

    def _field_from_source(
        self,
        source: Scope | exp.Table,
        column_name: str,
        query: exp.Expr,
    ) -> FieldDefinition | None:
        if isinstance(source, exp.Table):
            expression = table_expression(source)
            if expression is not None:
                function = self._schema_function_for_projection(
                    expression,
                )
                if function and isinstance(function.return_type, ModelDefinition):
                    return _field_in_model(function.return_type, column_name)
                return None

            field = self.db_schema.get_field(
                column_name,
                source.name,
                source.db or None,
            )
            if field:
                return field

            cte = cte_for_table(query, source)
            if cte:
                return self._field_from_projections(
                    statement_projections(cte.this),
                    column_name,
                    cte.this,
                )
            return None

        return self._field_from_projections(
            scope_projections(source),
            column_name,
            source.expression,
        )

    def _field_from_projections(
        self,
        projections: list[exp.Expr],
        column_name: str,
        context: exp.Expr,
    ) -> FieldDefinition | None:
        for projection in projections:
            if column_name in _projection_names(projection):
                return self.build_field(projection, context)

        return None

    def _unique_visible_field(
        self,
        column_name: str,
        query: exp.Expr,
    ) -> FieldDefinition | None:
        matches = [
            field
            for field in self._iter_visible_source_fields(column_name, query)
            if field is not None
        ]
        return matches[0] if len(matches) == 1 else None

    def _iter_visible_source_fields(
        self,
        column_name: str,
        query: exp.Expr,
    ) -> Iterator[FieldDefinition | None]:
        for scope in traverse_scope(query):
            for source in scope.sources.values():
                yield self._field_from_source(source, column_name, query)

    def _field_from_schema_function(
        self,
        item: exp.Expr,
        function: FunctionDefinition,
    ) -> FieldDefinition:
        return_type = function.return_type
        if isinstance(return_type, exp.DataType):
            return FieldDefinition(
                name=self.output_name(item),
                datatype=return_type.copy(),
            )

        if return_type is None:
            return FieldDefinition(
                name=self.output_name(item),
                datatype=exp.DataType.build(DType.UNKNOWN),
            )

        raise NormError(
            code=NormErrorCode.AMBIGUOUS_COLUMN,
            message="Couldn't infer the type of column",
            context={"column": str(item)},
        )

    def _schema_function_for_projection(
        self,
        expression: exp.Expr,
    ) -> FunctionDefinition | None:
        catalog_name, function_name, args = enclosing_schema_function_call(expression)
        return resolve_schema_function(
            self.db_schema,
            function_name,
            catalog_name,
            args,
        )

    def _find_source(
        self, source_name: str, query: exp.Expr
    ) -> Scope | exp.Table | None:
        for scope in reversed(list(traverse_scope(query))):
            source = scope.sources.get(source_name)
            if source:
                return cast("Scope | exp.Table", source)

        return None


def _field_in_model(
    model: ModelDefinition,
    column_name: str,
) -> FieldDefinition | None:
    field = model.fields.get(column_name)
    if field:
        return field

    for candidate in model.fields.values():
        if candidate.name.lower() == column_name.lower():
            return candidate

    return None


def _projection_source(item: exp.Expr) -> exp.Expr:
    return item.this if isinstance(item, exp.Alias) else item


def _column_name(expression: exp.Expr) -> str | None:
    if isinstance(expression, (exp.Column, exp.TableColumn)):
        return expression.name
    return None


def _function_name(expression: exp.Anonymous) -> str:
    return str(expression.name).lower()


def _is_auto_alias(alias: str) -> bool:
    return bool(_AUTO_ALIAS.fullmatch(alias))


def _default_projection_name(expression: exp.Expr) -> str | None:
    if isinstance(expression, exp.Alias):
        return _default_projection_name(expression.this)

    if isinstance(expression, exp.Column):
        return expression.name

    if isinstance(expression, exp.Count):
        return "count"

    if isinstance(expression, exp.Anonymous):
        return _function_name(expression)

    if isinstance(expression, exp.WithinGroup):
        return _default_projection_name(expression.this)

    if isinstance(expression, exp.PercentileDisc):
        return "percentile_disc"

    return expression.name or None


def _projection_names(projection: exp.Expr) -> list[str]:
    names = [projection.alias_or_name]

    if isinstance(projection, exp.Alias) and _is_auto_alias(projection.alias):
        default_name = _default_projection_name(projection.this)
        if default_name:
            names.insert(0, default_name)

    return [name for name in names if name]
