from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from typing import Literal
from urllib.parse import urlparse

from norm.consts import (
    SUPPORTED_POSTGRES_CONNECTION_SCHEMES,
    SUPPORTED_PYTHON_MODELS,
    SUPPORTED_SQL_DIALECTS,
)

IssueLoc = tuple[str | int, ...]


@dataclass
class ConfigIssue:
    loc: IssueLoc
    msg: str


class ConfigValidationError(Exception):
    def __init__(self, issues: list[ConfigIssue]):
        self.issues = issues
        super().__init__(self._to_message())

    def _to_message(self) -> str:
        return "; ".join(
            f"{' -> '.join(str(part) for part in issue.loc)}: {issue.msg}"
            for issue in self.issues
        )

    def errors(self) -> list[dict]:
        return [{"loc": issue.loc, "msg": issue.msg} for issue in self.issues]


def _validate_path_like(value: str, field_name: str) -> str:
    normalized = value.strip()
    if len(normalized) == 0:
        raise ValueError(f"{field_name} must be a non-empty path")

    if str(PurePath(normalized)) == ".":
        raise ValueError(f"{field_name} must be a valid path")

    return normalized


def _add_issue(issues: list[ConfigIssue], loc: IssueLoc, msg: str):
    issues.append(ConfigIssue(loc=loc, msg=msg))


def _parse_required_dict(
    data: dict,
    key: str,
    issues: list[ConfigIssue],
    loc: IssueLoc,
) -> dict | None:
    value = data.get(key)
    if value is None:
        _add_issue(issues, (*loc, key), "Field required")
        return None
    if not isinstance(value, dict):
        _add_issue(issues, (*loc, key), "Input should be a valid dictionary")
        return None
    return value


def _parse_string(
    value: object,
    issues: list[ConfigIssue],
    loc: IssueLoc,
    *,
    required: bool = True,
) -> str | None:
    if value is None:
        if required:
            _add_issue(issues, loc, "Field required")
        return None

    if not isinstance(value, str):
        _add_issue(issues, loc, "Input should be a valid string")
        return None
    return value


@dataclass
class SqlMigrations:
    connection: str | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict,
        issues: list[ConfigIssue],
        loc: IssueLoc,
    ) -> SqlMigrations | None:
        connection = data.get("connection")
        if connection is None:
            return cls(connection=None)

        if not isinstance(connection, str):
            _add_issue(issues, (*loc, "connection"), "Input should be a valid string")
            return None

        normalized = connection.strip()
        if len(normalized) == 0:
            _add_issue(
                issues,
                (*loc, "connection"),
                "'connection' must be a non-empty database URL",
            )
            return None

        parsed = urlparse(normalized)
        if parsed.scheme not in SUPPORTED_POSTGRES_CONNECTION_SCHEMES:
            supported = ", ".join(sorted(SUPPORTED_POSTGRES_CONNECTION_SCHEMES))
            _add_issue(
                issues,
                (*loc, "connection"),
                f"'connection' scheme must be one of: {supported}",
            )
            return None
        if parsed.hostname is None:
            _add_issue(issues, (*loc, "connection"), "'connection' must include a host")
            return None
        if parsed.path in {"", "/"}:
            _add_issue(
                issues,
                (*loc, "connection"),
                "'connection' must include a database name",
            )
            return None

        return cls(connection=normalized)


@dataclass
class SqlConfig:
    db_schema: str
    repositories: str
    engine: str
    migrations: SqlMigrations | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict,
        issues: list[ConfigIssue],
        loc: IssueLoc,
    ) -> SqlConfig | None:
        db_schema_value = _parse_string(
            data.get("db_schema"),
            issues,
            (*loc, "db_schema"),
        )
        db_schema = None
        if db_schema_value is not None:
            try:
                db_schema = _validate_path_like(db_schema_value, "db_schema")
                if db_schema.endswith(("/", "\\")):
                    raise ValueError("'db_schema' must point to a file path")
            except ValueError as err:
                _add_issue(issues, (*loc, "db_schema"), str(err))

        repositories_value = _parse_string(
            data.get("repositories"),
            issues,
            (*loc, "repositories"),
        )
        repositories = None
        if repositories_value is not None:
            try:
                repositories = _validate_path_like(repositories_value, "repositories")
            except ValueError as err:
                _add_issue(issues, (*loc, "repositories"), str(err))

        engine_value = _parse_string(data.get("engine"), issues, (*loc, "engine"))
        engine = None
        if engine_value is not None:
            engine = engine_value.strip().lower()
            if engine not in SUPPORTED_SQL_DIALECTS:
                supported = ", ".join(sorted(SUPPORTED_SQL_DIALECTS))
                _add_issue(
                    issues, (*loc, "engine"), f"'engine' must be one of: {supported}"
                )

        migrations_data = data.get("migrations")
        migrations = None
        if migrations_data is not None:
            if not isinstance(migrations_data, dict):
                _add_issue(
                    issues,
                    (*loc, "migrations"),
                    "Input should be a valid dictionary",
                )
            else:
                migrations = SqlMigrations.from_dict(
                    migrations_data,
                    issues,
                    (*loc, "migrations"),
                )

        if db_schema is None or repositories is None or engine is None:
            return None

        return cls(
            db_schema=db_schema,
            repositories=repositories,
            engine=engine,
            migrations=migrations,
        )


@dataclass
class PythonGenConfig:
    asynchronous: bool = True
    models: Literal["pydantic", "dataclasses"] = "pydantic"
    max_params: int = 1

    @classmethod
    def from_dict(
        cls,
        data: dict,
        issues: list[ConfigIssue],
        loc: IssueLoc,
    ) -> PythonGenConfig | None:
        asynchronous = data.get("asynchronous", True)
        if not isinstance(asynchronous, bool):
            _add_issue(
                issues, (*loc, "asynchronous"), "Input should be a valid boolean"
            )
            asynchronous = True

        models_value = data.get("models", "pydantic")
        models = _parse_string(models_value, issues, (*loc, "models"))
        normalized_models = None
        if models is not None:
            normalized_models = models.strip().lower()
            if normalized_models not in SUPPORTED_PYTHON_MODELS:
                supported = ", ".join(sorted(SUPPORTED_PYTHON_MODELS))
                _add_issue(
                    issues,
                    (*loc, "models"),
                    f"'models' must be one of: {supported}",
                )

        max_params = data.get("max_params", 1)
        if not isinstance(max_params, int):
            _add_issue(issues, (*loc, "max_params"), "Input should be a valid integer")
            max_params = 1

        if normalized_models is None:
            return None

        return cls(
            asynchronous=asynchronous,
            models=normalized_models,
            max_params=max_params,
        )


@dataclass
class GenConfig:
    out: str
    python: PythonGenConfig | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict,
        issues: list[ConfigIssue],
        loc: IssueLoc,
    ) -> GenConfig | None:
        out_value = _parse_string(data.get("out"), issues, (*loc, "out"))
        out = None
        if out_value is not None:
            try:
                out = _validate_path_like(out_value, "out")
            except ValueError as err:
                _add_issue(issues, (*loc, "out"), str(err))

        python_data = data.get("python")
        python = None
        if python_data is not None:
            if not isinstance(python_data, dict):
                _add_issue(
                    issues, (*loc, "python"), "Input should be a valid dictionary"
                )
            else:
                python = PythonGenConfig.from_dict(
                    python_data, issues, (*loc, "python")
                )

        if out is None:
            return None

        return cls(out=out, python=python)


@dataclass
class TargetConfig:
    name: str
    sql: SqlConfig
    gen: GenConfig

    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) == 0:
            raise ValueError("'name' must be a non-empty target name")
        return normalized

    @classmethod
    def from_dict(
        cls,
        data: dict,
        issues: list[ConfigIssue],
        loc: IssueLoc,
        name: str,
    ) -> TargetConfig | None:
        sql_data = _parse_required_dict(data, "sql", issues, loc)
        gen_data = _parse_required_dict(data, "gen", issues, loc)

        sql = SqlConfig.from_dict(sql_data, issues, (*loc, "sql")) if sql_data else None
        gen = GenConfig.from_dict(gen_data, issues, (*loc, "gen")) if gen_data else None

        if sql is None or gen is None:
            return None

        return cls(name=name, sql=sql, gen=gen)


@dataclass
class NormConfig:
    version: str
    targets: dict[str, TargetConfig]

    @classmethod
    def from_dict(cls, data: dict) -> NormConfig:
        issues: list[ConfigIssue] = []

        version = _parse_string(data.get("version"), issues, ("version",))
        normalized_version = None
        if version is not None:
            normalized_version = version.strip()
            if normalized_version != "1":
                _add_issue(issues, ("version",), "'version' must be '1'")

        targets_data = data.get("targets")
        targets: dict[str, TargetConfig] = {}
        if targets_data is None:
            _add_issue(issues, ("targets",), "Field required")
        elif not isinstance(targets_data, list):
            _add_issue(issues, ("targets",), "Input should be a valid list")
        elif len(targets_data) == 0:
            _add_issue(
                issues, ("targets",), "'targets' must include at least one target"
            )
        else:
            names: list[str] = []
            for index, target_data in enumerate(targets_data):
                if not isinstance(target_data, dict):
                    _add_issue(
                        issues,
                        ("targets", index),
                        "Input should be a valid dictionary",
                    )
                    continue

                raw_name = _parse_string(
                    target_data.get("name"),
                    issues,
                    ("targets", index, "name"),
                )
                if raw_name is None:
                    continue

                try:
                    target_name = TargetConfig.normalize_name(raw_name)
                except ValueError as err:
                    _add_issue(issues, ("targets", index, "name"), str(err))
                    continue

                names.append(target_name)
                target = TargetConfig.from_dict(
                    target_data,
                    issues,
                    ("targets", target_name),
                    target_name,
                )
                if target:
                    targets[target_name] = target

            duplicates = sorted({name for name in names if names.count(name) > 1})
            if duplicates:
                duplicates_text = ", ".join(duplicates)
                _add_issue(
                    issues,
                    ("targets",),
                    f"'targets' contains duplicate names: {duplicates_text}",
                )

        if issues:
            raise ConfigValidationError(issues)

        return cls(version=normalized_version, targets=targets)
