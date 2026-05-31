# Database and language support

This page is the canonical support matrix for engines and languages.

## Code generation

| Language | Python | Rust | Go | TypeScript |
| :--- | :---: | :---: | :---: | :---: |
| Postgres | ✅ | In progress | In progress | In progress |
| SQLite | ✅ | Roadmap | Roadmap | Roadmap |
| MySQL | ✅ | Roadmap | Roadmap | Roadmap |
| ClickHouse | ✅ | Roadmap | Roadmap | Roadmap |
| DuckDB | ✅ | Roadmap | Roadmap | Roadmap |

Python generation supports all five SQL engines. Set `sql.engine` in `norm.yaml` to match the target database.

## Schema pull (`norm schema pull`)

| Engine | Schema pull |
| :--- | :---: |
| Postgres | ✅ (`pg_dump`) |
| SQLite | — |
| MySQL | — |
| ClickHouse | — |
| DuckDB | — |

For non-Postgres engines, maintain `sql.db_schema` manually or import DDL from your migration system.

## Python model backends

| Backend | Support |
| :--- | :---: |
| `pydantic` | ✅ |
| `dataclasses` | ✅ |

Configure via `gen.python.models` in [Python configuration](./configuration/python).
