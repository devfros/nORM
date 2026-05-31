# `schema` - manage database schema

Manage database schema operations. The implemented subcommand today is `pull`.

## Pull schema from database

```sh
norm schema pull
norm schema pull --target default
norm schema pull -t default
```

### Options

- `--target`, `-t`: Pull schema for a specific target from `norm.yaml`.

### What it does

- Requires `sql.engine: postgres` on the target (other engines are rejected).
- Uses `sql.migrations.connection` from the selected target.
- Runs `pg_dump` in schema-only mode (includes `COMMENT ON` statements).
- Strips pg_dump/psql noise (`SET`, session config, psql meta commands).
- Parses the full pulled DDL in one pass and reformats every statement with sqlglot.
- Writes the result to `sql.db_schema`.
- Without `--target`, pulls schema for all targets (each must use `engine: postgres`).

### Requirements

- Target `sql.engine` must be `postgres`.
- `pg_dump` must be installed and available in `PATH`.
- Each target must provide `sql.migrations.connection` in config.

### Common errors

- Target uses an engine other than `postgres`.
- Missing `sql.migrations.connection`.
- `pg_dump` is not installed.
- Invalid connection URL or insufficient DB permissions.
- Pulled SQL cannot be parsed (unsupported or unexpected pg_dump output).
