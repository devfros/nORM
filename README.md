<div align="center">

# nORM

**Write the SQL you want. Generate the typed API you need.**

One tool for your database schema, queries, and typed data-layer code.

[![PyPI](https://img.shields.io/pypi/v/norm-cli)](https://pypi.org/project/norm-cli/)
[![Python](https://img.shields.io/pypi/pyversions/norm-cli)](https://pypi.org/project/norm-cli/)
[![License](https://img.shields.io/github/license/devfros/nORM)](LICENSE)

[Documentation](https://devfros.github.io/norm) · [Python tutorial](https://devfros.github.io/norm/tutorials/python) · [GitHub](https://github.com/devfros/norm)

</div>

nORM (**no ORM**) is a SQL-first toolkit for managing your database and the code that talks to it. You define schema and repository SQL in one place; nORM generates typed data access code for your stack. Python is available today. Rust, Go, and TypeScript generators are in progress, and a migrations workflow is planned, so the same `norm` CLI can eventually cover schema changes and repositories across languages.

If you like [sqlc](https://github.com/sqlc-dev/sqlc), the workflow will feel familiar: you keep writing real queries, and nORM removes the repetitive mapping code. It also adds helpers for dynamic filters, sorting, partial updates, and join embedding that are painful to maintain by hand.

## Example (Python)

**Schema** (`norm_in/schema.sql`):

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name text NOT NULL,
    blocked bool DEFAULT false
);
```

**Repository SQL** (`norm_in/repositories/users_repo.sql`):

```sql
-- repo_name: UsersRepo

-- name: get_user :one
SELECT * FROM users WHERE id = :id;

-- name: list_users :many
SELECT * FROM users ORDER BY name;
```

**Generated usage:**

```python
from norm_out.users_repo import UsersRepo

async with get_db() as db:
    repo = UsersRepo(db)
    user = await repo.get_user(id=42)       # User | None
    users = await repo.list_users()         # list[User]
```

Run `norm init` and `norm generate` to produce `norm_out/` with Pydantic models and async repository methods. The same SQL inputs will drive other language targets as they land. See the [Python tutorial](https://devfros.github.io/norm/tutorials/python) for config, CRUD, and project layout.

## Why nORM?

- **One workflow for schema and data layer.** Keep database definitions and repository SQL together instead of splitting schema management, query authoring, and hand-written mapping code across different tools.
- **SQL stays in charge.** Queries and execution plans stay visible; no ORM query builder in the middle.
- **Typed APIs from your SQL.** Parameters, return types, and row mapping are generated to match what you wrote.
- **Dynamic queries without string assembly.** Optional filters, sort orders, patch updates, and nested join shapes are expressed in SQL and compiled into safe, typed code.

## Dynamic filtering

Prefix a parameter with `_` to make it optional. One query can cover many filter combinations:

```sql
-- name: search_authors :many
SELECT * FROM authors
WHERE id = :_id OR rating > :rating;
```

```python
# rating is required; id is optional (defaults to UNSET)
await repo.search_authors(rating=4)
await repo.search_authors(rating=4, id=7)
```

[Dynamic filtering guide](https://devfros.github.io/norm/guides/dynamic_filtering) · [Dynamic sorting](https://devfros.github.io/norm/guides/dynamic_sorting) · [Partial updates](https://devfros.github.io/norm/guides/partial_update) · [Embedding models](https://devfros.github.io/norm/guides/embedding_models)

## Who this is for

**Good fit** if you want visible SQL, less boilerplate, strongly typed data access, and runtime filters without hand-built SQL strings.

**Not a fit** if you prefer designing queries through ORM method chains. Use SQLAlchemy or similar instead.

## Install

The CLI is a Python package today (requires **3.11+**). Install **`norm-cli`** from PyPI; the command on your PATH is **`norm`**:

```sh
pipx install norm-cli
norm --version
```

From a checkout: `pip install .` (same `norm` command).

## Quick start

```sh
norm init
# edit norm_in/schema.sql and norm_in/repositories/*.sql
norm generate
```

Other useful commands: `norm schema pull` (introspect Postgres), `norm check` (CI-friendly validation). See [commands](https://devfros.github.io/norm/commands/check). [Migrations](https://devfros.github.io/norm/commands/migrations) are planned.

## Language & database support

nORM is language-agnostic at the core: the same schema and repository SQL feed each code generator.

| Language             | Status        | Databases                                   |
| -------------------- | ------------- | ------------------------------------------- |
| Python               | Available     | Postgres, SQLite, MySQL, ClickHouse, DuckDB |
| Rust, Go, TypeScript | In progress   | TBD per target                              |

[Full support matrix](https://devfros.github.io/norm/reference/db_and_lang_support)

## Contributing

Bug reports, ideas, and PRs are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup and docs workflow.

## License

[MIT](LICENSE)
