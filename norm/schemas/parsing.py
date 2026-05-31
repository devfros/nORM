from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from sqlglot import Dialects, MappingSchema
from sqlglot.expressions import DataType

from norm.errors import NormError, NormErrorCode
from norm.schemas.core import CoreSchema
from norm.utils.switch_plurality import switch_plurality

DEFAULT_CATALOG_BY_DIALECT = {
    Dialects.POSTGRES: "public",
    Dialects.SQLITE: "main",
    Dialects.MYSQL: "default",
    Dialects.CLICKHOUSE: "default",
    Dialects.DUCKDB: "main",
}


class ModelKind(StrEnum):
    TABLE = "table"
    COMPOSITE = "composite"
    QUERY_RESULT = "query_result"
    VIEW = "view"
    MATERIALIZED_VIEW = "materialized_view"


class FunctionKind(StrEnum):
    FUNCTION = "function"
    MACRO = "macro"


class ParameterKind(StrEnum):
    BASIC = "basic"
    LIST = "list"
    PATCH_FLAG = "patch_flag"
    PATCH_TARGET = "patch_target"


class CatalogSource(StrEnum):
    IMPLICIT = "implicit"
    DECLARED = "declared"


@dataclass
class LiteralValue(CoreSchema):
    value: bool | str | None
    quoted: bool = False


@dataclass
class Constraints(CoreSchema):
    nullable: bool = False
    optional: bool = False
    default: LiteralValue | None = None


@dataclass
class ColumnRef(CoreSchema):
    name: str = field()
    table_name: str
    catalog_name: str | None = None
    alias: str | None = None
    table_alias: str | None = None


@dataclass
class FieldDefinition(CoreSchema):
    name: str
    datatype: DataType | ModelDefinition | None
    constraints: Constraints = field(default_factory=Constraints)
    column_ref: ColumnRef | None = None
    comment: str | None = None
    quoted: bool = False
    enum_type: EnumDefinition | None = field(default=None, metadata={"exclude": True})
    composite_type: ModelDefinition | None = field(
        default=None,
        metadata={"exclude": True},
    )

    @property
    def sql_datatype(self) -> DataType | None:
        if isinstance(self.datatype, DataType):
            return self.datatype
        return None

    @property
    def model_datatype(self) -> ModelDefinition | None:
        if not isinstance(self.datatype, ModelDefinition):
            return None
        return self.datatype


@dataclass
class ParameterDefinition(FieldDefinition):
    computed: bool = False
    kind: ParameterKind = ParameterKind.BASIC


@dataclass
class ModelDefinition(CoreSchema):
    name: str
    catalog_name: str | None = None
    fields: dict[str, FieldDefinition] = field(default_factory=dict)
    comment: str | None = None
    kind: ModelKind = ModelKind.QUERY_RESULT
    quoted: bool = False

    @property
    def model_name(self):
        return (
            switch_plurality(self.name) if self.kind == ModelKind.TABLE else self.name
        )


@dataclass
class FunctionDefinition(CoreSchema):
    name: str
    catalog_name: str | None = None
    parameters: dict[str, FieldDefinition] = field(default_factory=dict)
    return_type: DataType | ModelDefinition | None = None
    comment: str | None = None
    quoted: bool = False
    kind: FunctionKind = FunctionKind.FUNCTION


@dataclass
class EnumDefinition(CoreSchema):
    name: str
    values: list[LiteralValue] = field(default_factory=list)
    catalog_name: str | None = None
    comment: str | None = None
    quoted: bool = False


@dataclass
class CatalogDefinition(CoreSchema):
    name: str
    tables: dict[str, ModelDefinition] = field(default_factory=dict)
    views: dict[str, ModelDefinition] = field(default_factory=dict)
    functions: dict[str, dict[str, FunctionDefinition]] = field(default_factory=dict)
    enums: dict[str, EnumDefinition] = field(default_factory=dict)
    composite_types: dict[str, ModelDefinition] = field(default_factory=dict)
    comment: str | None = None
    source: CatalogSource = CatalogSource.IMPLICIT
    quoted: bool = False

    @property
    def declared(self) -> bool:
        return self.source == CatalogSource.DECLARED

    @declared.setter
    def declared(self, value: bool) -> None:
        self.source = CatalogSource.DECLARED if value else CatalogSource.IMPLICIT


@dataclass
class DBSchema(CoreSchema):
    dialect: Dialects
    default_catalog: str = "default"
    catalogs: dict[str, CatalogDefinition] = field(default_factory=dict)
    tables: dict[str, ModelDefinition] = field(
        default_factory=dict,
        metadata={"exclude": True},
    )

    def __post_init__(self) -> None:
        self.default_catalog = default_catalog_for_dialect(self.dialect)
        initial_tables = list(self.tables.values())
        self.tables = {}
        for table in initial_tables:
            self.add_table(table)

    def add_catalog(self, catalog_name: str | None = None) -> CatalogDefinition:
        name = catalog_name or self.default_catalog
        catalog = self.catalogs.get(name)
        if catalog is None:
            catalog = CatalogDefinition(name=name)
            self.catalogs[name] = catalog
        return catalog

    def declare_catalog(self, catalog_name: str) -> CatalogDefinition:
        catalog = self.catalogs.get(catalog_name)
        if catalog is None:
            catalog = CatalogDefinition(
                name=catalog_name,
                source=CatalogSource.DECLARED,
            )
            self.catalogs[catalog_name] = catalog
        else:
            catalog.source = CatalogSource.DECLARED
        return catalog

    def catalog_for_object(self, catalog_name: str | None) -> CatalogDefinition:
        name = catalog_name or self.default_catalog
        if name == self.default_catalog:
            return self.add_catalog(name)

        catalog = self.catalogs.get(name)
        if catalog is None or catalog.source != CatalogSource.DECLARED:
            raise NormError(
                code=NormErrorCode.UNDECLARED_CATALOG,
                message=f"Schema '{name}' is used but was not declared with CREATE SCHEMA.",
                hint=f"Add `CREATE SCHEMA {name};` before creating objects in that schema.",
                context={"catalog": name},
            )
        return catalog

    def add_table(self, table: ModelDefinition):
        catalog = self.catalog_for_object(table.catalog_name)
        table.catalog_name = catalog.name
        catalog.tables[table.name] = table
        self.tables[_qualified_name(catalog.name, table.name, self.default_catalog)] = (
            table
        )

    def add_enum(self, enum: EnumDefinition) -> None:
        catalog = self.catalog_for_object(enum.catalog_name)
        enum.catalog_name = catalog.name
        catalog.enums[enum.name] = enum

    def add_composite_type(self, composite_type: ModelDefinition) -> None:
        catalog = self.catalog_for_object(composite_type.catalog_name)
        composite_type.catalog_name = catalog.name
        catalog.composite_types[composite_type.name] = composite_type

    def add_view(self, view: ModelDefinition) -> None:
        catalog = self.catalog_for_object(view.catalog_name)
        view.catalog_name = catalog.name
        catalog.views[view.name] = view

    def add_function(self, function: FunctionDefinition) -> None:
        catalog = self.catalog_for_object(function.catalog_name)
        function.catalog_name = catalog.name
        signature = function_signature_key(function, dialect=self.dialect)
        overloads = catalog.functions.setdefault(function.name, {})
        overloads[signature] = function

    def get_table(
        self,
        name: str | None,
        catalog_name: str | None = None,
    ) -> ModelDefinition | None:
        from norm.schemas.resolver import SchemaResolver

        return SchemaResolver(self).table(name, catalog_name)

    def get_field(
        self,
        column_name: str,
        table_name: str | None,
        catalog_name: str | None = None,
    ) -> FieldDefinition | None:
        from norm.schemas.resolver import SchemaResolver

        return SchemaResolver(self).field(column_name, table_name, catalog_name)

    def get_enum(
        self,
        name: str | None,
        catalog_name: str | None = None,
    ) -> EnumDefinition | None:
        from norm.schemas.resolver import SchemaResolver

        return SchemaResolver(self).enum(name, catalog_name)

    def get_composite_type(
        self,
        name: str | None,
        catalog_name: str | None = None,
    ) -> ModelDefinition | None:
        from norm.schemas.resolver import SchemaResolver

        return SchemaResolver(self).composite_type(name, catalog_name)

    def get_view(
        self,
        name: str | None,
        catalog_name: str | None = None,
    ) -> ModelDefinition | None:
        from norm.schemas.resolver import SchemaResolver

        return SchemaResolver(self).view(name, catalog_name)

    def get_functions(
        self,
        name: str | None,
        catalog_name: str | None = None,
    ) -> list[FunctionDefinition]:
        from norm.schemas.resolver import SchemaResolver

        return SchemaResolver(self).functions(name, catalog_name)

    def get_function(
        self,
        name: str | None,
        catalog_name: str | None = None,
        *,
        signature: str | None = None,
    ) -> FunctionDefinition | None:
        from norm.schemas.resolver import SchemaResolver

        return SchemaResolver(self).function(name, catalog_name, signature=signature)

    def map(self) -> MappingSchema:
        from norm.schemas.sqlglot_mapping import build_mapping_schema

        return build_mapping_schema(self)

    def get_table_by_model_def(self, model: ModelDefinition) -> ModelDefinition | None:
        from norm.schemas.resolver import SchemaResolver

        return SchemaResolver(self).table_by_model_def(model)


def _qualified_name(catalog_name: str, name: str, default_catalog: str) -> str:
    if catalog_name == default_catalog:
        return name
    return f"{catalog_name}.{name}"


def default_catalog_for_dialect(dialect: Dialects) -> str:
    return DEFAULT_CATALOG_BY_DIALECT.get(dialect, "default")


_UNKNOWN_SIGNATURE_TYPE = "unknown"


def function_signature_key(
    function: FunctionDefinition,
    *,
    dialect: Dialects,
) -> str:
    type_names: list[str] = []
    for parameter in function.parameters.values():
        sql_datatype = parameter.sql_datatype
        if sql_datatype is None:
            type_names.append(_UNKNOWN_SIGNATURE_TYPE)
            continue
        type_names.append(sql_datatype.sql(dialect=dialect).lower())
    return ",".join(type_names)
