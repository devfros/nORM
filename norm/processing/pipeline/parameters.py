from __future__ import annotations

from typing import TYPE_CHECKING

from sqlglot import exp
from sqlglot.expressions import DType

from norm.consts import MetaKeys
from norm.errors import NormError, NormErrorCode
from norm.parsing.datatypes import enumcolumn_datatype, normalize_enum_datatype
from norm.parsing.dialect_capabilities import allows_typeless_columns
from norm.parsing.type_refs import resolve_enum_type
from norm.schemas.parsing import LiteralValue, ParameterDefinition, ParameterKind
from norm.utils.property_name import unique_property_name

if TYPE_CHECKING:
    from .context import ProcessingContext


class ParameterExtractionStage:
    def __init__(self, context: ProcessingContext) -> None:
        self.context = context

    def extract(self, query: exp.Expr) -> dict[str, ParameterDefinition]:
        result: dict[str, ParameterDefinition] = {}
        placeholders = query.find_all(exp.Placeholder)

        for ph in placeholders:
            name = ph.name
            datatype = ph.type

            if not datatype or (
                datatype.is_type(DType.UNKNOWN)
                and not allows_typeless_columns(self.context.dialect)
            ):
                raise NormError(
                    code=NormErrorCode.TYPE_INFERENCE_FAILED,
                    message=f"Type inference failed for query '{query.sql()}'",
                    hint=(
                        "Try explicit SQL casts or disambiguate columns/aliases "
                        "to make parameter types deterministic."
                    ),
                )

            metadata = ph.meta
            enum = resolve_enum_type(
                self.context.db_schema,
                datatype,
                metadata.get(MetaKeys.CATALOG_NAME),
            )

            if name in self.context.lists:
                old = datatype
                datatype = exp.DataType(this=DType.ARRAY)
                datatype.set("nested", True)
                datatype.set("expressions", [old])

            datatype = normalize_enum_datatype(datatype)

            nullable = metadata.get(MetaKeys.NULLABLE, False)
            optional = metadata.get(MetaKeys.OPTIONAL, False)
            kind = metadata.get(MetaKeys.PARAM_KIND, ParameterKind.BASIC)
            computed = kind == ParameterKind.PATCH_FLAG

            param = ParameterDefinition(
                name=name, datatype=datatype, computed=computed, kind=kind
            )
            param.constraints.nullable = nullable
            param.constraints.optional = optional
            if enum is not None:
                param.enum_type = enum

            if param.name not in result:
                result[param.name] = param
            elif result[param.name].sql_datatype and not result[
                param.name
            ].sql_datatype.is_type(datatype):
                raise NormError(
                    code=NormErrorCode.CONFLICTING_CONSTRAINTS,
                    message=f"Parameter '{param.name}' has conflicting constraints",
                    context={
                        "types": ", ".join(
                            [str(datatype), result[param.name].datatype.sql()]
                        ),
                    },
                )

        for item in self.context.ords.values():
            order_by = ParameterDefinition(
                name=item.order_by,
                datatype=enumcolumn_datatype(item.columns),
            )

            order_by.name = unique_property_name(result, order_by.name)
            result[order_by.name] = order_by
            item.order_by = order_by.name

            desc = ParameterDefinition(
                name=item.desc,
                datatype=exp.DataType.build(DType.BOOLEAN),
            )
            desc.constraints.default = LiteralValue(value=False)
            desc.name = unique_property_name(result, desc.name)
            result[desc.name] = desc
            item.desc = desc.name

        return result
