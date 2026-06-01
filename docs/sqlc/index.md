# sqlc

nORM is heavily inspired by [sqlc](https://github.com/sqlc-dev/sqlc).

If you already like SQL-first code generation, nORM should feel familiar: you keep writing SQL, and generated code gives your application typed access to the database.

## Why this page exists

`sqlc` is excellent. nORM is not trying to replace it outright.

nORM focuses on cases where you still reach for ORM-style workflows because they need more runtime composition.

## Where nORM adds extra ergonomics

- [Dynamic filtering](../guides/dynamic_filtering): compose `WHERE` logic safely at runtime
- [Dynamic sorting](../guides/dynamic_sorting): control `ORDER BY` dynamically with validated columns
- [Partial updates](../guides/partial_update): update only fields that were explicitly provided
- [Single named-parameter style](../guides/select#parameter-syntax): keep one query parameter style across dialects
- [Left-join embedding with `n.nembed()`](../guides/embedding_models): generate nullable nested models for `LEFT JOIN`
- [Migrations workflow](../commands/migrations): built-in migrations command group (currently in progress)

## Practical takeaway

If plain SQL plus generated types from `sqlc` already covers your needs, keep using it.

If you want SQL-first generation with the runtime composition features above, nORM is designed for that workflow.
