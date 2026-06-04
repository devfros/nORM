from pathlib import Path
from typing import cast

from jinja2 import Environment, PackageLoader
from jinja2.bccache import FileSystemBytecodeCache
from sqlglot import Dialects

from norm.consts import MODULE_COMMENT
from norm.gen.base_generator import BaseGenerator
from norm.gen.python.consts import UNSET_SENTINEL, VarNames
from norm.gen.python.dialects import PythonDialectProfile, get_python_dialect_profile
from norm.gen.python.naming import enum_values, model_class_name
from norm.gen.python.output_mapping import build_output_map, import_output_map_schemas
from norm.gen.python.schema_names import SchemaObjectNames
from norm.gen.python.schemas import ImportData, OutputIndexMap, PythonType
from norm.gen.python.types_map import get_python_type
from norm.gen.python.utils_funcs import get_required_utils
from norm.gen.spec import GenerationSpec
from norm.schemas import GenOutputFiles
from norm.schemas.config import GenConfig, PythonGenConfig
from norm.schemas.parsing import (
    CatalogDefinition,
    DBSchema,
    EnumDefinition,
    FieldDefinition,
    LiteralValue,
    ModelDefinition,
    ModelKind,
    ParameterKind,
)
from norm.schemas.repo import ProcessedQuery, Repo
from norm.utils.identifier import normalize_identifier
from norm.utils.switch_case import camel_to_snake

_JINJA_BCCACHE_DIR = Path.home() / ".cache" / "norm" / "jinja_bccache"


def _jinja_bytecode_cache() -> FileSystemBytecodeCache:
    _JINJA_BCCACHE_DIR.mkdir(parents=True, exist_ok=True)
    return FileSystemBytecodeCache(str(_JINJA_BCCACHE_DIR))


def _unique_sql_params(params: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for param in params:
        name = param["name"]
        if name in seen:
            continue
        seen.add(name)
        unique.append(param)
    return unique


def _function_return_annotation(return_type: PythonType, command: str) -> str:
    annotation = return_type.compiled
    if command == "one" and annotation != "None":
        annotation = f"{annotation} | None"
    if command == "many":
        annotation = f"list[{annotation}]"
    return annotation


def _catalogs_in_generation_order(db_schema: DBSchema) -> list[CatalogDefinition]:
    catalog_names = sorted(
        db_schema.catalogs,
        key=lambda name: (name != db_schema.default_catalog, name),
    )
    return [db_schema.catalogs.get(name) for name in catalog_names]  # pyright: ignore[reportReturnType]


class PythonGenerator(BaseGenerator):
    MODELS_FILE_NAME = "models"

    def __init__(self, config: GenConfig, dialect: Dialects):
        super().__init__(config, dialect)

        self.python: PythonGenConfig = cast("PythonGenConfig", config.python)

        self.templates = Environment(  # noqa: S701
            loader=PackageLoader("norm", "gen/python/templates"),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
            bytecode_cache=_jinja_bytecode_cache(),
            auto_reload=False,
        )

        self.var_names = VarNames()
        self.dialect_profile: PythonDialectProfile = get_python_dialect_profile(
            dialect, self.python.asynchronous
        )

        self._schema_names: SchemaObjectNames | None = None
        self._db_model_names: frozenset[str] = frozenset()

    def model_name(self, name: str) -> str:
        return model_class_name(name)

    def schema_class_name(self, model: ModelDefinition) -> str:
        if self._schema_names is not None:
            return self._schema_names.class_name(model)
        return self.model_name(model.model_name)

    def enum_class_name(self, enum: EnumDefinition) -> str:
        if self._schema_names is not None:
            return self._schema_names.enum_class_name(enum)
        return self.model_name(enum.name)

    def function_name(self, name: str) -> str:
        return camel_to_snake(name)

    def _get_field_python_type(
        self,
        field: FieldDefinition,
        models_module: str | None = None,
    ) -> PythonType:
        if field.composite_type:
            # Whole composite columns are opaque values from the driver (e.g. tuple/str).
            return PythonType(name="str")

        if field.enum_type:
            return PythonType(
                module=models_module,
                name=self.enum_class_name(field.enum_type),
            )

        if field.model_datatype:
            return PythonType(
                module=models_module
                if field.model_datatype.kind == ModelKind.TABLE
                else None,
                name=self.schema_class_name(field.model_datatype),
            )

        return get_python_type(field.sql_datatype, self.dialect_profile.dialect)

    def output_map(
        self,
        model: ModelDefinition,
        start_index: int = 0,
        nullable: bool = False,
    ) -> OutputIndexMap:
        return build_output_map(
            model=model,
            schema_name=self.schema_class_name,
            start_index=start_index,
            nullable=nullable,
        )

    def generate(self, db_schema: DBSchema, repos: list[Repo]) -> GenOutputFiles:
        generation_spec = GenerationSpec.from_inputs(db_schema, repos)
        output = GenOutputFiles()
        output.add_file(Path("__init__.py"), "")
        self._schema_names = SchemaObjectNames.from_db_schema(generation_spec.db_schema)
        self._db_model_names = self._collect_db_model_names(generation_spec.db_schema)

        output.add_file(
            Path(f"{self.MODELS_FILE_NAME}.py"),
            self._generate_db_models(generation_spec.db_schema),
        )

        utils = []
        for repo_spec in generation_spec.repos:
            imports = ImportData()

            repo_utils = get_required_utils(repo_spec.source)
            for util in repo_utils:
                imports.add_import(util.gen_import_module, util.gen_import_names)
            utils.extend(repo_utils)

            code = self._render_repo(repo_spec.source, imports)
            output.add_file(
                Path(f"{repo_spec.file_name}.py"),
                self._render_module(imports, code, MODULE_COMMENT),
            )

        for util in utils:
            util_module_path = Path(util.gen_module_name)
            util_module_init_path = Path(util_module_path, "__init__.py")

            util_file_name = util.gen_file_name
            util_path = Path(util_module_path, util_file_name)

            output.add_file(util_module_init_path, "")
            output.add_file(util_path, util.get_content())

        return output

    def _render_module(
        self, imports: ImportData, body: str, header_comment: str | None = None
    ) -> str:
        template = self.templates.get_template("common/module.jinja2")
        return template.render(
            header_comment=header_comment,
            imports=imports.sorted_imports(),
            body=body,
        )

    def _generate_db_models(self, db_schema: DBSchema) -> str:
        imports = ImportData()
        contents: list[str] = []
        for catalog in _catalogs_in_generation_order(db_schema):
            for enum in catalog.enums.values():
                contents.append(self._render_enum(enum, imports))

            for composite_type in catalog.composite_types.values():
                contents.append(self._render_schema(composite_type, imports))

            for table in catalog.tables.values():
                contents.append(self._render_schema(table, imports))

        content = ("\n" * 2).join(contents)
        return self._render_module(imports, content, MODULE_COMMENT)

    def _render_enum(self, enum_def: EnumDefinition, imports: ImportData) -> str:
        template = self.templates.get_template("models/enum.jinja2")
        imports.add_import("enum", ["StrEnum"])
        class_name = self.enum_class_name(enum_def)
        return template.render(
            name=class_name,
            comment=enum_def.comment,
            values=enum_values(enum_def, class_name),
        )

    def _render_schema(
        self,
        model_def: ModelDefinition,
        imports: ImportData,
        models_module: str | None = None,
    ) -> str:
        template = self.templates.get_template(
            f"models/{self.python.models}/model.jinja2"
        )
        if self.python.models == "pydantic":
            imports.add_import("pydantic", ["BaseModel"])
        elif self.python.models == "dataclasses":
            imports.add_import("dataclasses", ["dataclass"])

        fields = []
        for field_name, field in model_def.fields.items():
            nullable = field.constraints.nullable
            default = field.constraints.default

            python_type = self._get_field_python_type(field, models_module)

            if not default and field.model_datatype and nullable:
                default = LiteralValue(value=None)

            imports.merge(python_type.imports)
            fields.append(
                {
                    "name": normalize_identifier(field_name),
                    "type": python_type.compiled,
                    "nullable": nullable,
                    "default": default.to_dict() if default is not None else None,
                    "comment": field.comment,
                    "keywords": [],
                }
            )

        return template.render(
            name=self.schema_class_name(model_def),
            comment=model_def.comment,
            fields=fields,
        )

    def _render_repo(self, repo: Repo, imports: ImportData) -> str:
        template = self.templates.get_template("repo.jinja2")

        param_schemas: list[str] = []
        output_schemas: list[str] = []
        functions: list[str] = []

        imports.merge(self.dialect_profile.driver.imports)

        for query in repo.processed_queries:
            dto_schema_name = None
            if len(query.parameters) > self.python.max_params:
                param_schema = ModelDefinition(
                    name=f"{query.name}_params",
                    fields={},
                )
                for name, param in query.parameters.items():
                    if param.computed:
                        continue
                    field = param.model_copy()
                    if param.constraints.optional:
                        field.constraints.default = LiteralValue(UNSET_SENTINEL)
                    param_schema.fields[name] = field

                dto_schema_name = self.model_name(param_schema.model_name)
                param_schemas.append(
                    self._render_schema(
                        param_schema,
                        imports,
                        f".{self.MODELS_FILE_NAME}",
                    )
                )

            if (
                isinstance(query.returns, ModelDefinition)
                and query.returns.kind != ModelKind.TABLE
            ):
                query.returns.name = f"{query.name}_row"
                output_schemas.append(
                    self._render_schema(
                        query.returns,
                        imports,
                        f".{self.MODELS_FILE_NAME}",
                    )
                )

            functions.append(
                self._generate_function(
                    query,
                    dto_schema_name,
                    imports,
                    True,
                )
            )

        return template.render(
            name=repo.name,
            vars=self.var_names,
            functions=functions,
            query_row_schemas=output_schemas,
            param_schemas=param_schemas,
        )

    def _generate_function(
        self,
        processed_query: ProcessedQuery,
        dto_schema_name: str | None,
        imports: ImportData,
        is_class_method: bool = True,
    ) -> str:
        template = self.templates.get_template("function.jinja2")
        context = self._build_function_context(
            processed_query=processed_query,
            dto_schema_name=dto_schema_name,
            imports=imports,
            is_class_method=is_class_method,
        )

        return template.render(context=context, vars=self.var_names)

    def _build_function_context(
        self,
        processed_query: ProcessedQuery,
        dto_schema_name: str | None,
        imports: ImportData,
        is_class_method: bool,
    ) -> dict[str, object]:
        parameters = []
        optional_params = []
        sql_params = []
        is_dto_param = dto_schema_name is not None
        models_module = f".{self.MODELS_FILE_NAME}"

        for param in processed_query.parameters.values():
            if param.computed:
                continue

            param_type = self._get_field_python_type(param, models_module)
            imports.merge(param_type.imports)

            optional = param.constraints.optional
            default = param.constraints.default
            if optional:
                default = LiteralValue(value=UNSET_SENTINEL)

            param_object = {
                "name": param.name,
                "nullable": param.constraints.nullable,
                "optional": optional,
                "type": param_type.compiled,
                "default": default.to_dict() if default else None,
            }

            if optional:
                optional_params.append(
                    {
                        "name": param.name,
                        "expr": self._param_expr(param.name, is_dto_param),
                    }
                )
            parameters.append(param_object)

        if dto_schema_name:
            parameters = [
                {
                    "name": self.var_names.arg,
                    "nullable": False,
                    "optional": False,
                    "type": dto_schema_name,
                    "default": None,
                }
            ]

        parameters.sort(
            key=lambda item: (
                item["default"] is not None,
                item["nullable"],
            )
        )

        for param_name in processed_query.ordered_params_seq:
            param = processed_query.parameters.get(param_name)
            if not param:
                continue

            expr = param_name
            if param.kind == ParameterKind.PATCH_FLAG:
                expr = param_name.removesuffix("__is_set")

            sql_params.append(
                {
                    "name": param_name,
                    "expr": self._param_expr(expr, is_dto_param),
                    "kind": param.kind,
                }
            )

        is_async = self.python.asynchronous
        clear_sentinels = len(optional_params) > 0
        cursor_expr = (
            f"closing(self.{self.var_names.db}.cursor())"
            if self.dialect_profile.driver.close_sync_cursor
            else f"self.{self.var_names.db}.cursor()"
        )

        filter_map = (
            {key: value.dump() for key, value in processed_query.filters.items()}
            if processed_query.filters
            else None
        )

        if not processed_query.returns:
            return_type = PythonType(name="None")
        elif isinstance(processed_query.returns, FieldDefinition):
            return_type = self._get_field_python_type(
                processed_query.returns, models_module
            )
        else:
            return_type = self._get_field_python_type(
                FieldDefinition(
                    datatype=processed_query.returns,
                    name=self.model_name(processed_query.returns.model_name),
                ),
                models_module,
            )

        imports.merge(return_type.imports)

        output_map = None
        if isinstance(processed_query.returns, ModelDefinition):
            output_map = self.output_map(processed_query.returns)
            self._import_output_map_schemas(output_map, imports)

        command = processed_query.command.value
        driver = self.dialect_profile.driver
        return {
            "name": self.function_name(processed_query.name),
            "command": command,
            "comment": processed_query.comment,
            "is_class_method": is_class_method,
            "is_async": is_async,
            "query_str": processed_query.query_str,
            "cursor_expr": cursor_expr,
            "return_type": return_type.compiled,
            "return_annotation": _function_return_annotation(return_type, command),
            "output_map": output_map,
            "parameters": parameters,
            "optional_params": optional_params,
            "sql_query_params": (
                sql_params
                if not driver.named_params
                else _unique_sql_params(sql_params)
            ),
            "has_query_params": len(sql_params) > 0 or len(processed_query.lists) > 0,
            "named_params": driver.named_params,
            "sentinel": UNSET_SENTINEL,
            "clear_sentinels": clear_sentinels,
            "filter_map": filter_map,
            "list_modifiers": [
                {
                    "name": name,
                    "expr": self._param_expr(name, is_dto_param),
                    "key": key,
                }
                for name, key in processed_query.lists.items()
            ],
            "orderby_modifiers": [
                {
                    "key": key,
                    "columns": item.columns,
                    "order_by": item.order_by,
                    "order_by_expr": self._param_expr(item.order_by, is_dto_param),
                    "desc": item.desc,
                    "desc_expr": self._param_expr(item.desc, is_dto_param),
                }
                for key, item in processed_query.ords.items()
            ],
            "param_template": driver.param_template,
        }

    def _param_expr(self, name: str, is_dto_param: bool) -> str:
        if is_dto_param:
            return f"{self.var_names.arg}.{name}"
        return name

    def _collect_db_model_names(self, db_schema: DBSchema) -> frozenset[str]:
        names: set[str] = set()
        for catalog in db_schema.catalogs.values():
            for table in catalog.tables.values():
                names.add(self.schema_class_name(table))
            for composite_type in catalog.composite_types.values():
                names.add(self.schema_class_name(composite_type))
        return frozenset(names)

    def _import_output_map_schemas(
        self,
        output_map: OutputIndexMap,
        imports: ImportData,
    ) -> None:
        import_output_map_schemas(
            output_map=output_map,
            imports=imports,
            db_model_names=self._db_model_names,
            models_file_name=self.MODELS_FILE_NAME,
        )
