# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

--

## [0.1.0] - 2026-06-01

First public release. nORM is a SQL-first code generator for typed data access without ORM complexity - inspired by [sqlc](https://github.com/sqlc-dev/sqlc), with extra support for runtime query composition.

### Added

#### Code generation

- Python code generation from schema SQL and repository SQL files.
- Typed repository classes with methods for each annotated query.
- Model generation from schema DDL with **Pydantic** or **dataclasses** backends.
- Async (default) and sync repository generation modes.
- Query result commands: `:one`, `:many`, `:exec`, `:execrows`, and `:execlastid`.
- Params models for queries with many arguments (`gen.python.max_params`).
- Multi-target projects via `norm.yaml` (`targets[]` with independent SQL inputs and output paths).

#### Database support (Python)

- PostgreSQL, SQLite, MySQL, ClickHouse, and DuckDB.
- Dialect-specific Python drivers and type mapping for each engine.
- Unified named-parameter syntax (`:param`) across supported dialects.
- Postgres schema pull via `norm schema pull` (`pg_dump` integration).

#### SQL features and macros

- **Dynamic filtering** - optional predicates with `:_param` in `WHERE` and `HAVING`.
- **Partial updates** - patch-style `UPDATE` fields with `:_field`.
- **Dynamic sorting** - validated runtime `ORDER BY` via `n.ord(...)`.
- **Model embedding** - nested row shapes from joins via `n.embed()` and `n.nembed()`.
- Additional macros: `n.narg(:param)` for nullable arguments and `n.list(:param)` for `IN (...)` expansion.
- SQL parsing, type inference, column qualification, and return-field analysis powered by sqlglot.

#### CLI and tooling

- `norm init` - scaffold `norm.yaml`, input directories, and an empty schema file.
- `norm generate` - generate code from configured SQL sources.
- `norm check` - verify generated output is up to date (`--diff`, `--fix`, `--strict`).
- `norm targets` - list configured generation targets.
- `norm schema pull` - pull Postgres schema into `sql.db_schema`.
- Rich terminal output with `--verbose` / `--quiet` and `--no-color`.
- Machine-readable errors: `--error-format json` and `--error-format github` for CI.
- Click shell completion for config paths and target names.

#### Documentation and distribution

- Project website and docs at [devfros.github.io/nORM](https://devfros.github.io/nORM).
- MIT license.
- PyPI package **`norm-cli`** (`pipx/pip install norm-cli`); CLI command **`norm`**. Python 3.12–3.14.

#### In progress (included in repo, not yet production-ready)

- Go, Rust, and TypeScript code generators.
- `norm migrations` command group.

[Unreleased]: https://github.com/devfros/nORM/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/devfros/nORM/releases/tag/v0.1.0
