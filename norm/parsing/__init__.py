from .repo_parser import RepoSqlParser

__all__ = [
    "DdlModelBuilder",
    "RepoSqlParser",
    "SchemaSqlParser",
]


def __getattr__(name: str):
    if name == "DdlModelBuilder":
        from .ddl import DdlModelBuilder

        return DdlModelBuilder
    if name == "SchemaSqlParser":
        from .schema_parser import SchemaSqlParser

        return SchemaSqlParser
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
