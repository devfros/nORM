# Installation

## Requirements

- Python **3.12+** (for running the `norm` CLI and Python generation)
- A database driver for the engine used by generated code, such as `psycopg` for Postgres

## Install the CLI

Install the PyPI package **`norm-cli`**. The executable on your PATH is **`norm`**:

```shell
pipx install norm-cli
```

When working from a local checkout:

```shell
pip install .
# or: poetry install
```

## Verify

```shell
norm --version
```

## Optional runtime dependencies

Generated Python code imports the driver for the configured `sql.engine`. Install the driver that matches your target database:

| Engine | Typical async driver |
| :--- | :--- |
| Postgres | `psycopg[binary]` |
| SQLite | `aiosqlite` |
| MySQL | `asyncmy` |
| ClickHouse | `asynch` |
| DuckDB | `duckdb` |

## Next steps

- [Getting started with Python](../tutorials/python)
- [Configuration](../reference/configuration/)
- [Contributing](https://github.com/devfros/norm/blob/main/CONTRIBUTING.md) (local dev and docs preview)
