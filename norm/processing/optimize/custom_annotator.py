import typing as t

from sqlglot import exp
from sqlglot.optimizer.annotate_types import TypeAnnotator
from sqlglot.optimizer.scope import Scope

from norm.processing.function_sources import function_source_columns
from norm.processing.query_sources import (
    cte_for_table_in_scope,
    projection_output_names,
    scope_projections,
    statement_projections,
    table_expression,
)


class CustomTypeAnnotator(TypeAnnotator):
    def set_type(
        self, expression: exp.Expr, target_type: exp.DataType | exp.DType | None
    ) -> exp.Expr:
        return self._set_type(expression, target_type)

    def annotate_unknowns(self, expression: exp.Expr) -> exp.Expr:
        self._annotate_unknowns(expression)
        return expression

    def annotate_scope(self, scope: Scope) -> None:
        super().annotate_scope(scope)
        self._annotate_scope_unknown_outputs(scope)

    def _get_scope_source_selects(
        self,
        scope: Scope,
        source_name: str,
    ) -> dict[str, exp.DataType | exp.DType]:
        selects = dict(super()._get_scope_source_selects(scope, source_name))
        source = scope.sources.get(source_name)

        if isinstance(source, Scope):
            for projection in scope_projections(source):
                if projection.type and not projection.is_type(exp.DType.UNKNOWN):
                    for name in projection_output_names(projection):
                        selects.setdefault(name, projection.type)

        elif isinstance(source, exp.Table):
            selects.update(function_source_columns(source, self.schema.dialect))
            cte = cte_for_table_in_scope(scope, source)
            if cte:
                for projection in statement_projections(cte.this):
                    if projection.type and not projection.is_type(exp.DType.UNKNOWN):
                        for name in projection_output_names(projection):
                            selects.setdefault(name, projection.type)

        return selects

    def _annotate_scope_unknown_outputs(self, scope: Scope) -> None:
        expression = scope.expression
        if not isinstance(expression, exp.Selectable):
            return

        for projection in expression.selects or []:
            if projection.type and not projection.is_type(exp.DType.UNKNOWN):
                continue

            datatype = self._infer_type_from_scope(projection, scope)
            if datatype and not datatype.is_type(exp.DType.UNKNOWN):
                self._set_type(projection, datatype)
                if isinstance(projection, exp.Alias):
                    self._set_type(projection.this, datatype)

    def _infer_type_from_scope(
        self,
        expression: exp.Expr,
        scope: Scope,
    ) -> exp.DataType | None:
        datatype = expression.type
        if datatype and not datatype.is_type(exp.DType.UNKNOWN):
            return datatype

        if isinstance(expression, exp.Alias):
            return self._infer_type_from_scope(expression.this, scope)

        if isinstance(expression, exp.Coalesce):
            for item in [expression.this, *list(expression.expressions or [])]:
                datatype = self._infer_type_from_scope(item, scope)
                if datatype and not datatype.is_type(exp.DType.UNKNOWN):
                    return datatype
            return None

        if isinstance(expression, exp.Column):
            if expression.table:
                return self._source_column_type(
                    scope, expression.table, expression.name
                )

            return self._unique_visible_type(scope, expression.name)

        if isinstance(expression, exp.TableColumn):
            source = scope.sources.get(expression.name)
            if isinstance(source, exp.Table):
                table_expr = table_expression(source)
                if (
                    table_expr
                    and table_expr.type
                    and not table_expr.is_type(exp.DType.UNKNOWN)
                ):
                    return table_expr.type

            return self._unique_visible_type(scope, expression.name)

        return None

    def _source_column_type(
        self,
        scope: Scope,
        source_name: str,
        column_name: str,
    ) -> exp.DataType | None:
        source_scope: Scope | None = scope
        while source_scope:
            if source_name in source_scope.sources:
                datatype = self._get_scope_source_selects(
                    source_scope, source_name
                ).get(column_name)
                return datatype if isinstance(datatype, exp.DataType) else None

            source_scope = source_scope.parent

        return None

    def _unique_visible_type(
        self,
        scope: Scope,
        column_name: str,
    ) -> exp.DataType | None:
        matches = []
        for source_name in scope.sources:
            datatype = self._get_scope_source_selects(scope, source_name).get(
                column_name
            )
            if isinstance(datatype, exp.DataType):
                matches.append(datatype)

        return matches[0] if len(matches) == 1 else None

    def _annotate_unknowns(self, expression: exp.Expr) -> None:
        stack = [(expression, False)]

        while stack:
            expr, children_annotated = stack.pop()

            if not children_annotated:
                stack.append((expr, True))
                for child_expr in expr.iter_expressions():
                    stack.append((child_expr, False))
                continue

            if expr.type and not expr.is_type(exp.DType.UNKNOWN):
                continue

            spec = self.expression_metadata.get(expr.__class__)
            if spec and (annotator := spec.get("annotator")):
                annotator(self, expr)
            elif spec and (returns := spec.get("returns")):
                self._set_type(expr, returns)
            else:
                self._set_type(expr, exp.DType.UNKNOWN)

    def _set_type(
        self, expression: exp.Expr, target_type: exp.DataType | exp.DType | None
    ) -> exp.Expr:
        prev_type = expression.type
        expression_id = id(expression)

        dtype = target_type or exp.DType.UNKNOWN
        expression._type = (
            dtype if isinstance(dtype, exp.DataType) else dtype.into_expr()
        )
        self._visited.add(expression_id)

        if prev_type and t.cast("exp.DataType", prev_type).this == exp.DType.NULL:
            self._null_expressions.pop(expression_id, None)

        return expression
