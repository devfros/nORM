from pathlib import Path

from sqlglot import Dialects, exp, parse
from sqlglot.errors import ParseError

from norm.errors import NormError, NormErrorCode
from norm.schemas.parsing import DBSchema, ModelDefinition, function_signature_key

from .ddl import DdlModelBuilder, _literal_text
from .type_refs import resolve_schema_field_types
from .view_fields import populate_view_fields


class SchemaSqlParser:
    """Parse schema SQL files into a `DBSchema`."""

    def __init__(self, dialect: Dialects) -> None:
        self._dialect = dialect

    def parse_file(self, str_path: str | Path) -> DBSchema | None:
        with Path(str_path).open(mode="r") as sql_file:
            content = sql_file.read()

        return self.parse_sql(content)

    def parse_sql(self, content: str) -> DBSchema | None:
        if content is None or len(content) == 0:
            return None

        parsed = self._parse_statements(content)
        if parsed is None:
            return None

        create_defs = [item for item in parsed if isinstance(item, exp.Create)]
        comment_defs = [item for item in parsed if isinstance(item, exp.Comment)]
        if not create_defs and not comment_defs:
            return None

        db_schema: DBSchema = DBSchema(dialect=self._dialect)

        visited_tables: set[str] = set()
        visited_views: set[str] = set()
        visited_functions: set[str] = set()
        pending_views: list[tuple[ModelDefinition, exp.Expr | None, list[str]]] = []
        for create_def in create_defs:
            kind = create_def.kind.lower() if create_def.kind else None
            if kind == "schema":
                schema = create_def.find(exp.Table)
                if schema:
                    db_schema.declare_catalog(schema.db or schema.name)
                continue

            if kind == "table":
                table = create_def.find(exp.Table)
                if not table:
                    continue

                catalog_name = table.db or db_schema.default_catalog
                table_key = f"{catalog_name}.{table.name}"
                if table_key in visited_tables:
                    raise NormError(
                        code=NormErrorCode.DUPLICATE_TABLE,
                        message=f"Duplicate table in schema '{table.name}'.",
                        hint="Keep one CREATE TABLE statement per table name.",
                        context={"table": table.name},
                    )
                visited_tables.add(table_key)

                model = DdlModelBuilder.model_from_create_table(
                    create_def, dialect=self._dialect
                )
                if model and len(model.fields.keys()) > 0:
                    db_schema.add_table(model)
                continue

            if kind == "view":
                table, column_names = _table_from_create_def(create_def)
                if not table:
                    continue

                catalog_name = table.db or db_schema.default_catalog
                view_key = f"{catalog_name}.{table.name}"
                if view_key in visited_views:
                    raise NormError(
                        code=NormErrorCode.DUPLICATE_VIEW,
                        message=f"Duplicate view in schema '{table.name}'.",
                        hint="Keep one CREATE VIEW statement per view name.",
                        context={"view": table.name},
                    )
                visited_views.add(view_key)

                view = DdlModelBuilder.model_from_create_view(create_def)
                if view:
                    db_schema.add_view(view)
                    pending_views.append(
                        (view, create_def.expression, column_names),
                    )
                continue

            if kind in {"function", "macro"}:
                if kind == "macro":
                    callable_def = DdlModelBuilder.macro_from_create(
                        create_def, dialect=self._dialect
                    )
                else:
                    callable_def = DdlModelBuilder.function_from_create(
                        create_def, dialect=self._dialect
                    )
                if not callable_def:
                    continue

                catalog_name = callable_def.catalog_name or db_schema.default_catalog
                signature = function_signature_key(callable_def, dialect=self._dialect)
                callable_key = f"{catalog_name}.{callable_def.name}.{signature}"
                if callable_key in visited_functions:
                    raise NormError(
                        code=NormErrorCode.DUPLICATE_FUNCTION,
                        message=(
                            f"Duplicate function signature for '{callable_def.name}'."
                        ),
                        hint=(
                            "Each CREATE FUNCTION or MACRO must have a unique argument "
                            "type signature within the same schema."
                        ),
                        context={
                            "function": callable_def.name,
                            "signature": signature,
                        },
                    )
                visited_functions.add(callable_key)
                db_schema.add_function(callable_def)
                continue

            if kind == "type":
                enum = DdlModelBuilder.enum_from_create_type(create_def)
                if enum:
                    db_schema.add_enum(enum)
                    continue

                composite_type = DdlModelBuilder.model_from_create_composite_type(
                    create_def, dialect=self._dialect
                )
                if composite_type:
                    db_schema.add_composite_type(composite_type)

        for view, query, column_names in pending_views:
            populate_view_fields(view, query, column_names, db_schema)

        for comment_def in comment_defs:
            self._apply_comment(db_schema, comment_def)

        resolve_schema_field_types(db_schema)

        return db_schema

    def _parse_statements(self, sql_string: str) -> list[exp.Expr] | None:
        try:
            parsed = parse(sql=sql_string, dialect=self._dialect)
        except ParseError as err:
            raise NormError(
                code=NormErrorCode.SQL_PARSE_FAILED,
                message="Failed to parse schema SQL.",
                context={"details": str(err)},
            ) from err
        return parsed

    def parse_create_defs(self, sql_string: str) -> list[exp.Create] | None:
        parsed = self._parse_statements(sql_string)
        if parsed is None:
            return None

        return [item for item in parsed if isinstance(item, exp.Create)]

    def parse_table_defs(self, sql_string: str) -> list[exp.Create] | None:
        create_defs = self.parse_create_defs(sql_string)
        if create_defs is None:
            return None

        table_defs: list[exp.Create] = [
            item
            for item in create_defs
            if item and item.kind and item.kind.lower() == "table"
        ]
        return table_defs

    def _apply_comment(self, db_schema: DBSchema, comment: exp.Comment) -> None:
        raw_kind = comment.args.get("kind")
        kind = raw_kind.upper() if isinstance(raw_kind, str) else None
        text = _literal_text(comment.expression)
        if not kind or text is None:
            return

        target = comment.this

        if kind == "SCHEMA":
            if isinstance(target, exp.Table) and target.name:
                db_schema.declare_catalog(target.name).comment = text
            return

        if kind == "TYPE":
            if isinstance(target, exp.Table) and target.name:
                catalog_name = target.db or db_schema.default_catalog
                enum = db_schema.get_enum(target.name, catalog_name)
                if enum:
                    enum.comment = text
                    return

                composite_type = db_schema.get_composite_type(
                    target.name,
                    catalog_name,
                )
                if composite_type:
                    composite_type.comment = text
            return

        if kind == "VIEW":
            if isinstance(target, exp.Table) and target.name:
                catalog_name = target.db or db_schema.default_catalog
                view = db_schema.get_view(target.name, catalog_name)
                if view:
                    view.comment = text
            return

        if kind == "TABLE":
            if isinstance(target, exp.Table) and target.name:
                catalog_name = target.db or db_schema.default_catalog
                table = db_schema.get_table(target.name, catalog_name)
                if table:
                    table.comment = text
            return

        if kind == "COLUMN" and isinstance(target, exp.Column):
            column_name = target.name
            table_name = target.table
            if not column_name or not table_name:
                return

            catalog_name = target.db or db_schema.default_catalog
            table = db_schema.get_table(table_name, catalog_name)
            if table and column_name in table.fields:
                table.fields[column_name].comment = text


def _table_from_create_def(
    create_def: exp.Create,
) -> tuple[exp.Table | None, list[str]]:
    from norm.parsing.ddl import _table_from_create_this

    return _table_from_create_this(create_def.this)
