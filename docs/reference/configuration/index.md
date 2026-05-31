# Configuration

nORM reads project configuration from `norm.yaml` in the project root.

## Quick start template

`norm init` writes a default `norm.yaml` from the bundled template:

```yaml [norm.yaml]
version: "1"

targets:
  - name: default

    sql:
      engine: postgres
      db_schema: ./norm_in/schema.sql
      repositories: ./norm_in/repositories

    gen:
      out: ./norm_out
      python:
        asynchronous: true
        models: pydantic
        max_params: 10
```

Add `sql.migrations.connection` when a target needs [schema pull](../../commands/schema):

```yaml
      migrations:
        connection: postgresql://user:password@localhost:5432/mydb
```

## What `norm init` creates

| Setting | Default | Notes |
| :--- | :--- | :--- |
| `sql.engine` | `postgres` | Also supported: `sqlite`, `mysql`, `clickhouse`, `duckdb` |
| `sql.db_schema` | `./norm_in/schema.sql` | Empty file if missing |
| `sql.repositories` | `./norm_in/repositories` | Directory for `*.sql` query files |
| `gen.out` | `./norm_out` | Wiped and regenerated on each `norm generate` |
| `gen.python.asynchronous` | `true` | Set `false` for [sync generation](./python#sync) |
| `gen.python.models` | `pydantic` | Or `dataclasses` |
| `gen.python.max_params` | `10` | Params models appear when a query has more than this many arguments |

The template does not include `migrations.connection` until you add it for `norm schema pull`.

## Top-level fields

### `version`

- Required.

### `targets`

- Required.
- Must contain at least one target.
- Target names must be unique.

Each item in `targets` describes one generation target: SQL inputs plus generated output.

## `targets[].name`

- Required.
- Non-empty string.
- Used by CLI flags like `norm generate --target <name>` and `norm schema pull --target <name>`.

## `targets[].sql`

Defines SQL input sources and database settings.

### `targets[].sql.engine`

- Required.
- Supported values: `postgres`, `sqlite`, `mysql`, `clickhouse`, `duckdb`.
- Drives SQL parsing, type mapping, and generated driver code for Python.

### `targets[].sql.db_schema`

- Required.
- Path to a SQL schema file (not a directory path).
- Used during generation as the table/type source.

### `targets[].sql.repositories`

- Required.
- Path to a directory containing repository `*.sql` files.
- `norm generate` parses all `*.sql` files from this directory.

### `targets[].sql.migrations.connection`

- Optional.
- Required only for `norm schema pull` (not for `norm migrations`, which is not implemented yet).
- Must be a non-empty PostgreSQL connection URL:
  - scheme: `postgres://` or `postgresql://`
  - must include host
  - must include database name

## `targets[].gen`

Defines where generated code is written and which language generator is used.

### `targets[].gen.out`

- Required.
- Output directory path for generated code.
- `norm generate` removes this directory before writing fresh output.

Generated Python layout (typical):

```text
norm_out/
├── __init__.py
├── models.py
├── users_repo.py
└── _utils/          # only when needed (dynamic filter, partial update, etc.)
```

### `targets[].gen.python`

- Optional in the config schema, but required for Python output.
- Python is the only fully supported generator today.
- Field-level options are documented in [Python configuration](./python).

## Multi-target example

Use multiple targets when different services, packages, or environments need isolated SQL inputs and generated output.

```yaml [norm.yaml]
version: "1"

targets:
  - name: api
    sql:
      engine: postgres
      db_schema: ./services/api/norm_in/schema.sql
      repositories: ./services/api/norm_in/repositories
    gen:
      out: ./services/api/norm_out
      python:
        asynchronous: true
        models: pydantic
        max_params: 1

  - name: worker
    sql:
      engine: postgres
      db_schema: ./services/worker/norm_in/schema.sql
      repositories: ./services/worker/norm_in/repositories
      migrations:
        connection: postgresql://user:password@localhost:5432/worker_db
    gen:
      out: ./services/worker/norm_out
      python:
        asynchronous: false
        models: dataclasses
        max_params: 3
```

## How commands use config

- `norm init`
  - creates `norm.yaml` if missing
  - creates each target's `sql.repositories` directory
  - creates parent directories for `sql.db_schema` and touches the schema file
- `norm generate`
  - reads `sql.db_schema` and `sql.repositories`
  - writes generated output into `gen.out`
- `norm schema pull`
  - requires `sql.engine: postgres` on the target (pull uses `pg_dump`)
  - requires `sql.migrations.connection`
  - pulls schema through `pg_dump`, reformats it with sqlglot, and writes it to `sql.db_schema`

Related command docs:

- [init](../../commands/init)
- [generate](../../commands/generate)
- [schema](../../commands/schema)

## Common config errors

- **No targets or duplicate names**
  - define at least one target and make each `name` unique.
- **Unsupported values**
  - `sql.engine` must be one of the supported dialects above.
  - `gen.python.models` must be `pydantic` or `dataclasses`.
- **Invalid migration URL**
  - use `postgres://` or `postgresql://`, include host and database.

If parsing or validation fails, nORM reports `Invalid norm.yaml configuration.` with field-level details for the exact key that needs attention.
