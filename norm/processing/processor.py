from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from norm.processing.extracting import (
    get_ordered_parameter_sequence,
)
from norm.processing.optimize import optimize_query
from norm.processing.pipeline import (
    DynamicFilterStage,
    ParameterExtractionStage,
    PostprocessStage,
    PreprocessStage,
    ProcessingContext,
    ReturnExtractionStage,
)
from norm.processing.return_fields import ReturnFieldResolver
from norm.schemas.repo import ProcessedQuery

if TYPE_CHECKING:
    from sqlglot import exp

    from norm.schemas.dynamic_filter import DynamicFilter
    from norm.schemas.parsing import (
        DBSchema,
        FieldDefinition,
        ParameterDefinition,
    )
    from norm.schemas.repo import DynamicOrderby, RepoQuery


class ProcessorFn(Protocol):
    def __call__(
        self,
        query: exp.Expr,
    ) -> exp.Expr: ...


class QueryProcessor:
    def __init__(
        self,
        db_schema: DBSchema,
        param_template: str = "?",
        preprocessors: list[ProcessorFn] | None = None,
        postprocessors: list[ProcessorFn] | None = None,
        enforce_dynamic_filtering: bool = False,
    ) -> None:
        self.context = ProcessingContext(
            db_schema=db_schema,
            enforce_dynamic_filtering=enforce_dynamic_filtering,
            param_template=param_template,
        )
        self.db_schema = self.context.db_schema
        self.dialect = self.context.dialect
        self.enforce_dynamic_filtering = enforce_dynamic_filtering
        self.return_field_resolver = ReturnFieldResolver(self.db_schema)
        self.dynamic_filter_stage = DynamicFilterStage(self.context)
        self.parameter_extraction_stage = ParameterExtractionStage(self.context)
        self.postprocess_stage = PostprocessStage(self.context)
        self.preprocess_stage = PreprocessStage(self.context)
        self.return_extraction_stage = ReturnExtractionStage(
            self.context,
            self.return_field_resolver,
        )

        self.PREPROCESSORS: list[ProcessorFn] = preprocessors or [
            self.preprocess_stage.validate_macros,
            self.preprocess_stage.preprocess_nargs,
            self.preprocess_stage.preprocess_placeholders,
            self.preprocess_stage.preprocess_ords,
            self.preprocess_stage.preprocess_lists,
            self.preprocess_stage.preprocess_embeds,
            self.preprocess_stage.preprocess_patches,
            self.preprocess_stage.preprocess_wildcards,
        ]

        self.POSTROCESSORS: list[ProcessorFn] = postprocessors or [
            self.postprocess_stage.lists,
            self.postprocess_stage.placeholders,
            self.postprocess_stage.projections,
        ]
        self._reset_temporary_data()

    def _reset_temporary_data(self) -> None:
        self.context.reset_state()
        self._lists: dict[str, str] = self.context.lists
        self._patches: dict[str, str] = self.context.patches
        self._ords: dict[str, DynamicOrderby] = self.context.ords
        self._filters: dict[str, DynamicFilter] = self.context.filters

    def process(self, repo_query: RepoQuery) -> ProcessedQuery:
        self._reset_temporary_data()

        query = self.preprocess(repo_query.sql)

        ordered_param_seq = get_ordered_parameter_sequence(query, self.dialect)

        optimized_query = optimize_query(
            query.copy(),
            schema=self.db_schema.map(),
            dialect=self.dialect,
            db_schema=self.db_schema,
        )

        returns = self.return_extraction_stage.extract_returns(
            optimized_query, repo_query
        )

        parameters = self.extract_parameters(optimized_query)

        query = self.dynamic_filter(query)

        query = self.postprocess(query)

        query_str = query.sql(
            pretty=True, comments=True, max_text_width=50, dialect=self.dialect
        )

        return ProcessedQuery(
            name=repo_query.name,
            command=repo_query.command,
            comment=repo_query.comment,
            query_str=query_str,
            lists=self._lists,
            patches=self._patches,
            ords=self._ords,
            filters=self._filters,
            parameters=parameters,
            ordered_params_seq=ordered_param_seq,
            returns=returns,
        )

    def preprocess(self, query: exp.Expr) -> exp.Expr:
        """
        Preprocess SQL query
        """
        preprocessed_query = query.copy()
        for preprocess_func in self.PREPROCESSORS:
            preprocess_func(preprocessed_query)

        return preprocessed_query

    def postprocess(self, query: exp.Expr):
        """
        Postprocess SQL query
        """
        postprocessed_query = query.copy()
        for postprocess_func in self.POSTROCESSORS:
            postprocess_func(postprocessed_query)

        return postprocessed_query

    def dynamic_filter(
        self, query: exp.Expr, with_postprocessing: bool = True
    ) -> exp.Expr:
        def postprocess_callback(expr: exp.Expr) -> exp.Expr:
            return self.postprocess(expr)

        return self.dynamic_filter_stage.process(
            query,
            with_postprocessing=with_postprocessing,
            postprocess=postprocess_callback,
        )

    def extract_return_fields(self, query: exp.Expr) -> list[FieldDefinition]:
        return self.return_extraction_stage.extract_return_fields(query)

    def extract_parameters(self, query: exp.Expr) -> dict[str, ParameterDefinition]:
        return self.parameter_extraction_stage.extract(query)
