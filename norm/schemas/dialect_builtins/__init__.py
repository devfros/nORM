__all__ = [
    "merge_postgres_builtin_schema_map",
    "postgres_builtin_field",
]


def __getattr__(name: str):
    if name in __all__:
        from norm.schemas.dialect_builtins import postgres

        return getattr(postgres, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
