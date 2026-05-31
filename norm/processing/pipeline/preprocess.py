from __future__ import annotations

from typing import TYPE_CHECKING

from sqlglot import exp

from norm.consts import (
    OPTIONAL_PREFIX,
    TEMP_PLACEHOLDER_PATTERN,
    MetaKeys,
)
from norm.errors import NormError, NormErrorCode, unknown_column, unknown_table
from norm.macros import (
    INVALID_USE_ERROR_MSG,
    EmbedMacro,
    ListMacro,
    NargMacro,
    NembedMacro,
    NormMacro,
    NormMacrosEnum,
    OrdMacro,
)
from norm.processing.function_sources import expand_function_stars
from norm.processing.optimize.qualify_columns import qualify_columns
from norm.schemas.parsing import ParameterKind
from norm.schemas.repo import DynamicOrderby

if TYPE_CHECKING:
    from norm.schemas.parsing import ModelDefinition

    from .context import ProcessingContext


class PreprocessStage:
    def __init__(self, context: ProcessingContext) -> None:
        self.context = context

    def validate_macros(self, query: exp.Expr) -> exp.Expr:
        """
        Validates all macros signatures to catch nested usage (e.g `n.narg(n.list(:ids))`).
        """
        all_macros: list[type[NormMacro]] = [
            ListMacro,
            NargMacro,
            EmbedMacro,
            NembedMacro,
            OrdMacro,
        ]
        for macro in all_macros:
            macro.extract_all_from(query)

        return query

    def preprocess_placeholders(self, query: exp.Expr) -> exp.Expr:
        """
        :_param -> :param.
        """
        for ph in query.find_all(exp.Placeholder):
            ph.meta[MetaKeys.OPTIONAL] = ph.name.startswith(OPTIONAL_PREFIX)
            ph.set("this", ph.name.strip().lstrip(OPTIONAL_PREFIX))

        return query

    def preprocess_embeds(self, query: exp.Expr) -> exp.Expr:
        """
        n.embed(a) -> a.* (with additional metadata for further development).
        """
        if not isinstance(query, exp.Select):
            return query

        if len(query.expressions) == 0:
            return query

        new_expressions = []
        for expr in query.expressions:
            item = expr
            alias = None

            if isinstance(expr, exp.Alias):
                item = expr.this
                alias = expr.alias

            embed_macro = EmbedMacro.extract_from(item)
            embed_macro = embed_macro or NembedMacro.extract_from(item)

            if embed_macro:
                if embed_macro.macro_name == NormMacrosEnum.EMBED:
                    nullable = False
                else:
                    nullable = True

                meta_node = exp.Alias(this=exp.Identifier(this="#"))
                embed_meta = {"nullable": nullable, "alias": alias}
                meta_node.meta[MetaKeys.EMBED] = embed_meta

                new_expressions.append(meta_node)
                new_expressions.append(
                    exp.Column(
                        this=exp.Star(),
                        table=exp.Identifier(this=embed_macro.name),
                    )
                )
                new_expressions.append(meta_node.copy())
            else:
                new_expressions.append(expr)

        query.set("expressions", new_expressions)

        return query

    def _handle_set_item(
        self,
        table: ModelDefinition,
        col: exp.Column,
        expression: exp.Expr,
    ) -> None:
        column_name = col.name
        column = table.fields.get(column_name)
        if not column:
            raise unknown_column(column_name, table.name)

        if not isinstance(expression, exp.Placeholder) or not expression.meta.get(
            MetaKeys.OPTIONAL
        ):
            return

        name = expression.name
        is_set_name = f"{name}__is_set"

        self.context.patches[is_set_name] = name

        name_ph = exp.Placeholder(this=name)
        name_ph.meta[MetaKeys.OPTIONAL] = name
        name_ph.meta[MetaKeys.PARAM_KIND] = ParameterKind.PATCH_TARGET

        is_set_ph = exp.Placeholder(this=is_set_name)
        is_set_ph.meta[MetaKeys.PARAM_KIND] = ParameterKind.PATCH_FLAG

        if column.constraints.nullable:
            condition = is_set_ph
        else:
            condition = exp.And(
                this=is_set_ph,
                expression=exp.Not(
                    this=exp.Is(
                        this=exp.Cast(
                            this=name_ph,
                            to=column.sql_datatype,
                        ),
                        expression=exp.Null(),
                    )
                ),
            )

        case = exp.Case(
            ifs=[exp.If(this=condition, true=name_ph)],
            default=exp.Column(this=exp.Identifier(this=column_name)),
        )

        expression.replace(case)

    def preprocess_patches(self, query: exp.Expr) -> exp.Expr:
        """
        Replace patches with CASE statement.
        """
        updates = list(query.find_all(exp.Update, bfs=False))

        for update in updates:
            table_name = update.this.name

            table = self.context.db_schema.get_table(table_name)
            if not table:
                raise unknown_table(table_name)

            for item in update.expressions:
                if not isinstance(item, exp.EQ):
                    continue

                # NOTE: set multiple (postgres)
                if isinstance(item.this, exp.Tuple) and isinstance(
                    item.expression, exp.Tuple
                ):
                    for col, expression in zip(
                        item.this.expressions,
                        item.expression.expressions,
                        strict=True,
                    ):
                        self._handle_set_item(table, col, expression)

                elif isinstance(item.this, exp.Column):
                    self._handle_set_item(table, item.this, item.expression)

        return query

    def preprocess_lists(self, query: exp.Expr) -> exp.Expr:
        """
        Replace lists with placeholders + metadata.
        """
        macros = ListMacro.extract_all_from(query)
        for ind, list_macro in enumerate(macros):
            name = list_macro.name

            ph = exp.Placeholder(this=name)
            key = f"LIST{ind + 1}"
            ph.meta[MetaKeys.LIST_KEY] = key
            ph.meta[MetaKeys.PARAM_KIND] = ParameterKind.LIST
            self.context.lists[name] = key

            list_macro.expr.replace(ph)

        return query

    def preprocess_nargs(self, query: exp.Expr) -> exp.Expr:
        """
        Replace nargs (nullable parameters) with placeholders + metadata.
        """
        macros = NargMacro.extract_all_from(query)
        for narg_macro in macros:
            ph = exp.Placeholder(this=narg_macro.name)
            ph.meta[MetaKeys.NULLABLE] = True
            narg_macro.expr.replace(ph)

        return query

    def preprocess_ords(self, query: exp.Expr) -> exp.Expr:
        """
        Process dynamic ORDER BY.
        """
        macros = OrdMacro.extract_all_from(query)
        for ind, ord_macro in enumerate(macros):
            macro = ord_macro.expr
            table_name_or_alias_needed = f"Table name or alias needed for {macro}"

            table_name = None
            table_alias = None

            order = macro.find_ancestor(exp.Order)
            tables = []
            if order and order.parent:
                # TODO: Maybe not the best way
                tables = list(order.parent.find_all(exp.Table) or [])

            # if table name provided
            if ord_macro.table and ord_macro.table != "_":
                name = ord_macro.table
                for table in tables:
                    if name in [table.name, table.alias]:
                        table_name = table.name
                        table_alias = table.alias
                        break
                if not table_name and not table_alias:
                    raise unknown_table(name)

            # if table name is not provided, checking if only single table involved
            if not table_name and len(list(tables)) == 1:
                table_name = tables[0].name
                table_alias = tables[0].alias

            if table_name is None:
                raise NormError(
                    code=NormErrorCode.INVALID_MACRO_USAGE,
                    message=table_name_or_alias_needed,
                    hint="Use n.ord(table_name_or_alias) and ensure table exists in query.",
                    context={"macro": str(macro)},
                )

            table = self.context.db_schema.get_table(table_name)
            if table is None:
                raise unknown_table(table_name)

            order_obj = DynamicOrderby(
                columns=[field.name for field in table.fields.values()],
                table_name=table_name,
            )
            key = f"ORDER{ind + 1}"

            self.context.ords[key] = order_obj

            if ord_macro.order_by:
                order_obj.order_by = ord_macro.order_by
            if ord_macro.desc:
                order_obj.desc = ord_macro.desc

            order_by = macro.find_ancestor(exp.Ordered)

            if order_by is None:
                raise NormError(
                    code=NormErrorCode.INVALID_MACRO_USAGE,
                    message=INVALID_USE_ERROR_MSG.format(macro),
                    hint="Use n.ord(...) inside an ORDER BY expression.",
                    context={"macro": str(macro)},
                )

            new_order_by = exp.Ordered(
                this=exp.Identifier(this=TEMP_PLACEHOLDER_PATTERN.format(key)),
                nulls_first=True,
            )
            order_by.replace(new_order_by)

        return query

    def preprocess_wildcards(self, query: exp.Expr) -> exp.Expr:
        """
        Expand all wildcards in projections (sqlglot optimizer rule).
        """
        query = qualify_columns(
            query,
            schema=self.context.db_schema.map(),
            dialect=self.context.dialect,
        )
        return expand_function_stars(query, self.context.dialect)
