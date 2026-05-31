from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlglot import exp
from sqlglot.expressions import DType

from norm.consts import MetaKeys
from norm.errors import NormError, NormErrorCode
from norm.processing.extracting import get_projection_expressions
from norm.schemas.parsing import FieldDefinition, ModelDefinition
from norm.schemas.repo import QueryCommandEnum
from norm.utils.property_name import unique_property_name
from norm.utils.switch_plurality import switch_plurality

if TYPE_CHECKING:
    from norm.processing.return_fields import ReturnFieldResolver
    from norm.schemas.repo import RepoQuery

    from .context import ProcessingContext


class ReturnExtractionStage:
    def __init__(
        self,
        context: ProcessingContext,
        return_field_resolver: ReturnFieldResolver,
    ) -> None:
        self.context = context
        self.return_field_resolver = return_field_resolver

    def _build_field_def(self, item: exp.Expr, query: exp.Expr) -> FieldDefinition:
        if not isinstance(item, (exp.Column, exp.Alias, exp.TableColumn)):
            raise NormError(
                code=NormErrorCode.AMBIGUOUS_COLUMN,
                message="Unexpected projection",
                context={"projection": str(item)},
            )

        return self.return_field_resolver.build_field(item, query)

    def extract_returns(
        self,
        query: exp.Expr,
        repo_query: RepoQuery,
    ) -> FieldDefinition | ModelDefinition | None:
        command = repo_query.command
        if command == QueryCommandEnum.EXEC:
            return None

        if command in [
            QueryCommandEnum.EXECROWS,
            QueryCommandEnum.EXECLASTID,
        ]:
            return FieldDefinition(
                name=command,
                datatype=exp.DataType.build(DType.INT),
            )

        return_fields = self.extract_return_fields(query)

        if len(return_fields) == 0:
            # if no returnings, make exec command
            repo_query.command = QueryCommandEnum.EXEC
            return None

        if len(return_fields) == 1:
            return return_fields[0]

        returns = ModelDefinition(name="_override_me_", fields={})
        for field in return_fields:
            unique_name = unique_property_name(returns.fields.keys(), field.name)
            returns.fields[unique_name] = field

        return self.context.db_schema.get_table_by_model_def(returns) or returns

    def extract_return_fields(self, query: exp.Expr) -> list[FieldDefinition]:
        result: list[FieldDefinition] = []

        projections = get_projection_expressions(query)
        visited: set[int] = set()

        for ind, item in enumerate(projections):
            if ind in visited:
                continue

            visited.add(ind)

            if MetaKeys.EMBED not in item.meta:
                result.append(self._build_field_def(item, query))
                continue

            embed_field = None
            for j in range(ind + 1, len(projections)):
                visited.add(j)
                embed_item = projections[j]

                if MetaKeys.EMBED in embed_item.meta:
                    break

                if embed_field:
                    continue

                embed_field = self._build_field_def(embed_item, query)

            if not embed_field or not embed_field.column_ref:
                raise NormError(
                    code=NormErrorCode.OUTPUT_SCHEMA_RESOLUTION_FAILED,
                    message=f"No table information for return column '{item.alias_or_name}'.",
                    hint="Qualify the column with a table alias or use an explicit alias.",
                )

            table = self.context.db_schema.get_table(embed_field.column_ref.table_name)
            table = cast("ModelDefinition", table)

            meta = item.meta[MetaKeys.EMBED]
            alias = meta.get("alias")
            embed_field.constraints.nullable = meta.get("nullable")
            embed_field.column_ref = None
            embed_field.datatype = table
            embed_field.name = alias or switch_plurality(table.name)
            result.append(embed_field)

        return result
