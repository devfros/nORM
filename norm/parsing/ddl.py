from sqlglot import Dialects, exp

from norm.parsing.datatypes import enum_literals_from_datatype, normalize_enum_datatype
from norm.parsing.dialect_capabilities import allows_typeless_columns
from norm.schemas.parsing import (
    ColumnRef,
    Constraints,
    EnumDefinition,
    FieldDefinition,
    FunctionDefinition,
    FunctionKind,
    LiteralValue,
    ModelDefinition,
    ModelKind,
)

_TYPELESS_COLUMN_TYPE = exp.DataType.build("UNKNOWN")


class DdlModelBuilder:
    @staticmethod
    def field_from_column_def(
        column_def: exp.ColumnDef,
        table: exp.Table | None = None,
        *,
        dialect: Dialects,
    ) -> FieldDefinition | None:
        if not column_def.kind:
            if not allows_typeless_columns(dialect):
                return None
            datatype = _TYPELESS_COLUMN_TYPE
        else:
            datatype = column_def.kind

        nullable = True
        if column_def.kind:
            nullable = column_def.kind.args.get("nullable", nullable)

        default = None
        comment = None
        for constraint in column_def.constraints:
            if constraint.find(
                exp.NotNullColumnConstraint, exp.PrimaryKeyColumnConstraint
            ):
                nullable = False
            comment_constraint = constraint.find(exp.CommentColumnConstraint)
            if comment_constraint:
                comment = _literal_text(comment_constraint.this)

        column = None
        if table:
            column = ColumnRef(
                name=column_def.name,
                catalog_name=_catalog_name_from_table(table),
                alias=column_def.alias or None,
                table_name=table.name,
                table_alias=table.alias or None,
            )

        datatype = normalize_enum_datatype(datatype)

        field = FieldDefinition(
            name=column_def.name,
            datatype=datatype,
            constraints=Constraints(
                nullable=nullable,
                default=default,
            ),
            column_ref=column,
            comment=comment,
            quoted=_is_quoted_identifier(column_def.this),
        )

        return field

    @staticmethod
    def field_from_typeless_column(
        column_name: exp.Identifier,
        table: exp.Table,
    ) -> FieldDefinition:
        column = ColumnRef(
            name=column_name.name,
            catalog_name=_catalog_name_from_table(table),
            table_name=table.name,
            table_alias=table.alias or None,
        )
        field = FieldDefinition(
            name=column_name.name,
            datatype=_TYPELESS_COLUMN_TYPE,
            constraints=Constraints(nullable=True),
            column_ref=column,
            quoted=_is_quoted_identifier(column_name),
        )
        return field

    @staticmethod
    def model_from_create_table(
        table_def: exp.Create,
        *,
        dialect: Dialects,
    ) -> ModelDefinition | None:
        table = table_def.find(exp.Table)
        if not table:
            return None

        spec = ModelDefinition(
            name=table.name,
            catalog_name=_catalog_name_from_table(table),
            fields={},
            comment=_schema_comment(table_def),
            kind=ModelKind.TABLE,
            quoted=_is_quoted_identifier(table.this),
        )

        schema = table_def.find(exp.Schema)
        if isinstance(schema, exp.Schema):
            for item in schema.expressions or []:
                if isinstance(item, exp.ColumnDef):
                    field = DdlModelBuilder.field_from_column_def(
                        item, table, dialect=dialect
                    )
                    if field:
                        spec.fields[field.name] = field
                    continue

                if allows_typeless_columns(dialect) and isinstance(
                    item, exp.Identifier
                ):
                    if item.name in spec.fields:
                        continue
                    spec.fields[item.name] = DdlModelBuilder.field_from_typeless_column(
                        item, table
                    )
        else:
            for item in table_def.find_all(exp.ColumnDef):
                if not item:
                    continue

                field = DdlModelBuilder.field_from_column_def(
                    item, table, dialect=dialect
                )
                if field:
                    spec.fields[field.name] = field

        if len(spec.fields.keys()) == 0:
            return None

        return spec

    @staticmethod
    def enum_from_create_type(type_def: exp.Create) -> EnumDefinition | None:
        type_name = type_def.find(exp.Table)
        expression = type_def.args.get("expression")
        if not type_name or not isinstance(expression, exp.DataType):
            return None

        values = _literal_values_from_enum_datatype(expression)
        if not values:
            return None

        enum = EnumDefinition(
            name=type_name.name,
            values=values,
            catalog_name=_catalog_name_from_table(type_name),
            quoted=_is_quoted_identifier(type_name.this),
        )

        return enum

    @staticmethod
    def model_from_create_composite_type(
        type_def: exp.Create,
        *,
        dialect: Dialects,
    ) -> ModelDefinition | None:
        type_name = type_def.find(exp.Table)
        expression = type_def.args.get("expression")
        if not type_name or not isinstance(expression, exp.Schema):
            return None

        spec = ModelDefinition(
            name=type_name.name,
            catalog_name=_catalog_name_from_table(type_name),
            fields={},
            kind=ModelKind.COMPOSITE,
            quoted=_is_quoted_identifier(type_name.this),
        )

        for item in expression.find_all(exp.ColumnDef):
            field = DdlModelBuilder.field_from_column_def(item, dialect=dialect)
            if field:
                spec.fields[field.name] = field

        if len(spec.fields.keys()) == 0:
            return None

        return spec

    @staticmethod
    def model_from_create_view(view_def: exp.Create) -> ModelDefinition | None:
        table, column_names = _table_from_create_this(view_def.this)
        if not table:
            return None

        kind = (
            ModelKind.MATERIALIZED_VIEW
            if _is_materialized_view(view_def)
            else ModelKind.VIEW
        )
        return ModelDefinition(
            name=table.name,
            catalog_name=_catalog_name_from_table(table),
            fields={},
            comment=_schema_comment(view_def),
            kind=kind,
            quoted=_is_quoted_identifier(table.this),
        )

    @staticmethod
    def function_from_create(
        function_def: exp.Create,
        *,
        dialect: Dialects,
    ) -> FunctionDefinition | None:
        if dialect == Dialects.CLICKHOUSE:
            clickhouse_function = DdlModelBuilder.clickhouse_function_from_create(
                function_def,
                dialect=dialect,
            )
            if clickhouse_function:
                return clickhouse_function

        udf = function_def.this
        if not isinstance(udf, exp.UserDefinedFunction):
            return None

        table = udf.this
        if not isinstance(table, exp.Table):
            return None

        parameters = _parameters_from_udf(udf, dialect=dialect)

        return FunctionDefinition(
            name=table.name,
            catalog_name=_catalog_name_from_table(table),
            parameters=parameters,
            return_type=_return_type_from_create(function_def, dialect=dialect),
            comment=_schema_comment(function_def),
            quoted=_is_quoted_identifier(table.this),
            kind=FunctionKind.FUNCTION,
        )

    @staticmethod
    def macro_from_create(
        macro_def: exp.Create,
        *,
        dialect: Dialects,
    ) -> FunctionDefinition | None:
        udf = macro_def.this
        if not isinstance(udf, exp.UserDefinedFunction):
            return None

        table = udf.this
        if not isinstance(table, exp.Table):
            return None

        return FunctionDefinition(
            name=table.name,
            catalog_name=_catalog_name_from_table(table),
            parameters=_parameters_from_udf(udf, dialect=dialect),
            comment=_schema_comment(macro_def),
            quoted=_is_quoted_identifier(table.this),
            kind=FunctionKind.MACRO,
        )

    @staticmethod
    def clickhouse_function_from_create(
        function_def: exp.Create,
        *,
        dialect: Dialects,
    ) -> FunctionDefinition | None:
        table = function_def.this
        if not isinstance(table, exp.Table):
            return None

        parameters, return_type = _clickhouse_signature_from_expression(
            function_def.expression,
            dialect=dialect,
        )

        return FunctionDefinition(
            name=table.name,
            catalog_name=_catalog_name_from_table(table),
            parameters=parameters,
            return_type=return_type,
            comment=_schema_comment(function_def),
            quoted=_is_quoted_identifier(table.this),
            kind=FunctionKind.FUNCTION,
        )


def _table_from_create_this(
    this: exp.Expr | None,
) -> tuple[exp.Table | None, list[str]]:
    if isinstance(this, exp.Schema):
        table = this.this if isinstance(this.this, exp.Table) else None
        column_names = [
            item.name
            for item in this.expressions or []
            if isinstance(item, exp.Identifier)
        ]
        return table, column_names

    if isinstance(this, exp.Table):
        return this, []

    return None, []


def _parameters_from_udf(
    udf: exp.UserDefinedFunction,
    *,
    dialect: Dialects,
) -> dict[str, FieldDefinition]:
    parameters: dict[str, FieldDefinition] = {}
    for item in udf.expressions or []:
        if isinstance(item, exp.ColumnDef):
            field = DdlModelBuilder.field_from_column_def(item, dialect=dialect)
            if field and field.name not in parameters:
                parameters[field.name] = field
            continue

        if isinstance(item, exp.Identifier) and item.name not in parameters:
            parameters[item.name] = FieldDefinition(
                name=item.name,
                datatype=_TYPELESS_COLUMN_TYPE,
                constraints=Constraints(nullable=True),
                quoted=_is_quoted_identifier(item),
            )
    return parameters


def _clickhouse_signature_from_expression(
    expression: exp.Expr | None,
    *,
    dialect: Dialects,
) -> tuple[dict[str, FieldDefinition], exp.DataType | ModelDefinition | None]:
    if expression is None:
        return {}, None

    lambda_expr = (
        expression
        if isinstance(expression, exp.Lambda)
        else expression.find(exp.Lambda)
    )
    if isinstance(lambda_expr, exp.Lambda):
        return _parameters_from_clickhouse_lambda(lambda_expr), None

    json_extract = (
        expression
        if isinstance(expression, exp.JSONExtract)
        else expression.find(exp.JSONExtract)
    )
    if isinstance(json_extract, exp.JSONExtract):
        parameters = _parameters_from_clickhouse_tuple(
            json_extract.this, dialect=dialect
        )
        return parameters, _return_type_from_clickhouse_json_extract(json_extract)

    return {}, None


def _parameters_from_clickhouse_lambda(
    lambda_expr: exp.Lambda,
) -> dict[str, FieldDefinition]:
    parameters: dict[str, FieldDefinition] = {}
    for item in lambda_expr.expressions or []:
        if isinstance(item, exp.Identifier) and item.name not in parameters:
            parameters[item.name] = FieldDefinition(
                name=item.name,
                datatype=_TYPELESS_COLUMN_TYPE,
                constraints=Constraints(nullable=True),
                quoted=_is_quoted_identifier(item),
            )
    return parameters


def _parameters_from_clickhouse_tuple(
    node: exp.Expr | None,
    *,
    dialect: Dialects,
) -> dict[str, FieldDefinition]:
    if isinstance(node, exp.Paren):
        node = node.this

    if not isinstance(node, exp.Tuple):
        return {}

    parameters: dict[str, FieldDefinition] = {}
    for item in node.expressions or []:
        if isinstance(item, exp.Alias) and isinstance(item.this, exp.Column):
            datatype = (
                exp.DataType.build(item.alias) if item.alias else _TYPELESS_COLUMN_TYPE
            )
            parameters[item.this.name] = FieldDefinition(
                name=item.this.name,
                datatype=datatype,
                constraints=Constraints(nullable=True),
            )
            continue

        if isinstance(item, exp.Identifier) and item.name not in parameters:
            parameters[item.name] = FieldDefinition(
                name=item.name,
                datatype=_TYPELESS_COLUMN_TYPE,
                constraints=Constraints(nullable=True),
                quoted=_is_quoted_identifier(item),
            )
            continue

        if isinstance(item, exp.ColumnDef):
            field = DdlModelBuilder.field_from_column_def(item, dialect=dialect)
            if field and field.name not in parameters:
                parameters[field.name] = field

    return parameters


def _return_type_from_clickhouse_json_extract(
    json_extract: exp.JSONExtract,
) -> exp.DataType | None:
    return_expr = json_extract.expression
    if isinstance(return_expr, exp.Column):
        return_expr = return_expr.this

    if isinstance(return_expr, exp.Identifier):
        try:
            return exp.DataType.build(return_expr.name)
        except Exception:
            return None

    return None


def _is_materialized_view(create_def: exp.Create) -> bool:
    properties = create_def.args.get("properties")
    if not isinstance(properties, exp.Properties):
        return False
    return properties.find(exp.MaterializedProperty) is not None


def _return_type_from_create(
    create_def: exp.Create,
    *,
    dialect: Dialects,
) -> exp.DataType | ModelDefinition | None:
    returns_property = create_def.find(exp.ReturnsProperty)
    if not returns_property:
        return None

    expression = returns_property.this
    if isinstance(expression, exp.DataType):
        return normalize_enum_datatype(expression)

    if isinstance(expression, exp.Schema):
        spec = ModelDefinition(
            name="_return_",
            fields={},
            kind=ModelKind.QUERY_RESULT,
        )
        for item in expression.find_all(exp.ColumnDef):
            field = DdlModelBuilder.field_from_column_def(item, dialect=dialect)
            if field:
                spec.fields[field.name] = field
        if spec.fields:
            return spec

    return None


def _literal_values_from_enum_datatype(
    datatype: exp.DataType,
) -> list[LiteralValue] | None:
    literals = enum_literals_from_datatype(datatype)
    if not literals:
        return None

    values = [
        LiteralValue(value=str(literal.this), quoted=bool(literal.is_string))
        for literal in literals
    ]
    return values or None


def _is_quoted_identifier(expression: exp.Expr) -> bool:
    return isinstance(expression, exp.Identifier) and bool(
        expression.args.get("quoted")
    )


def _catalog_name_from_table(table: exp.Table) -> str | None:
    return table.db or None


def _schema_comment(table_def: exp.Create) -> str | None:
    properties = table_def.args.get("properties")
    if not isinstance(properties, exp.Properties):
        return None

    comment_property = properties.find(exp.SchemaCommentProperty)
    if not comment_property:
        return None

    return _literal_text(comment_property.this)


def _literal_text(expression: exp.Expr | None) -> str | None:
    if isinstance(expression, exp.Literal):
        return str(expression.this)
    return None
