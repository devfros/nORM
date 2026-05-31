SUPPORTED_SQL_DIALECTS = frozenset(
    {"postgres", "sqlite", "mysql", "clickhouse", "duckdb"}
)
SUPPORTED_PYTHON_MODELS = frozenset({"pydantic", "dataclasses"})

# Connection schemes accepted while postgres is the only supported engine.
SUPPORTED_POSTGRES_CONNECTION_SCHEMES = frozenset({"postgres", "postgresql"})
