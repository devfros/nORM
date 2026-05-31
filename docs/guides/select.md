# Fetching records

In nORM, reads start as ordinary SQL. Add a query annotation, run code generation, and nORM turns the result shape into typed code.

## Start with normal SQL

Without parameters:

```sql
-- name: list_authors :many
SELECT * FROM authors;
```

With a parameter:

```sql
-- name: get_author_by_id :one
SELECT * FROM authors
WHERE id = :id;
```

## Return mode: `:one`, `:many`, `:exec`

Choose the return mode from the behavior the generated method should expose:

- `:one`: return at most one row
- `:many`: return multiple rows
- `:exec`: run query without returning rows

See [Query annotations](../reference/annotations) for `:execrows` and `:execlastid`.

For a typical Postgres target, nORM generates the following shape:

```sql [authors_repo.sql]
-- name: list_authors :many
SELECT * FROM authors;

-- name: get_author_by_id :one
SELECT * FROM authors
WHERE id = :id;
```

::: code-group

```python [example.py]
async def list_authors(
    self,
) -> list[Author]:
    query = """
        SELECT
          authors.id AS id,
          authors.name AS name,
          authors.rating AS rating
        FROM authors
    """

    async with self.db.cursor() as cur:
        await cur.execute(query)
        result = [
            Author(
                id=item[0],
                name=item[1],
                rating=item[2],
            )
            async for item in cur
        ]

    return result

async def get_author_by_id(
    self,
    id: int,
) -> Author | None:
    query = """
        SELECT
          authors.id AS id,
          authors.name AS name,
          authors.rating AS rating
        FROM authors
        WHERE
          authors.id = %(id)s
    """

    params = {
        "id": id,
    }

    async with self.db.cursor() as cur:
        await cur.execute(query, params)
        result = await cur.fetchone()
        if result is None:
            return None

        result = Author(
            id=result[0],
            name=result[1],
            rating=result[2],
        )

    return result
```

```go [example.go]
// coming soon
```

```rust [example.rs]
// coming soon
```

```typescript [example.ts]
// coming soon
```

:::

## Wildcard expansion (`SELECT *`)

Using `*` is fine while writing repository SQL.
nORM expands wildcards during generation, so the generated SQL still maps explicit columns into typed models.

## How nORM chooses return schema

For row results, nORM chooses one of two schemas:

- If the query returns every column from exactly one table, and nothing else, nORM reuses that table model.
- Otherwise, nORM generates a query-specific row model.

Generated row schema names use the query name:

- `<QueryName>Row` in PascalCase.
- Example: `list_author_summaries` becomes `ListAuthorSummariesRow`.

## Parameter syntax

Use named parameters in repository SQL:

- `:id`
- `:limit`
- `:offset`

nORM rewrites those placeholders for the target driver. For Postgres-generated Python, the final SQL string uses `%(name)s`.

## `max_params` and generated function signatures

`max_params` controls when nORM groups parameters into a single input model instead of many separate function arguments.

::: code-group

```python [example.py]
# max_params: 1 with two query params -> grouped params model
class CreateUserParams(BaseModel):
    name: str
    blocked: bool | None

async def create_user(self, arg: CreateUserParams) -> None: ...
```

```go [example.go]
// coming soon
```

```rust [example.rs]
// coming soon
```

```typescript [example.ts]
// coming soon
```

:::

## Type inference and casts

nORM infers parameter types, nullability, and result types from the schema and query context.
When SQL leaves a type ambiguous, cast explicitly:

```sql
-- name: list_authors_min_rating :many
SELECT * FROM authors
WHERE rating >= :min_rating::int;
```

## Nullable arguments with `n.narg()`

nORM infers nullable parameters in many cases.
Use `n.narg()` when the query itself should mark a parameter as nullable.

```sql
-- name: get_author :one
SELECT * FROM authors a
WHERE a.id = n.narg(:id);
```

## List arguments with `n.list()`

Use `n.list()` when one logical parameter represents multiple values, such as an `IN` filter. This is especially useful for dialects that do not support array-style bindings like `id IN (:ids::int[])`.

```sql
-- name: get_authors :many
SELECT authors.name AS name
FROM authors
WHERE authors.id IN (n.list(:ids));
```

## Related guides

- [Embedding models](./embedding_models)
- [Dynamic filtering](./dynamic_filtering)
- [Dynamic sorting](./dynamic_sorting)
- [Query annotations](../reference/annotations)
