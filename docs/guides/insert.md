# Inserting records

## Basic insert (`:exec`)

Use `:exec` when the caller only needs the write to happen and does not need returned rows.

```sql
-- name: create_user :exec
INSERT INTO users (
  name, blocked
) VALUES (
  :name, :blocked
);
```

::: code-group

```python [example.py]
async def create_user(
    self,
    arg: CreateUserParams,
) -> None:
    query = """
        INSERT INTO users (
          name,
          blocked
        )
        VALUES
          (%(name)s, %(blocked)s)
    """

    params = {
        "name": arg.name,
        "blocked": arg.blocked,
    }

    async with self.db.cursor() as cur:
        await cur.execute(query, params)

        result = None

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

## Insert and return the created row

Use `RETURNING` when the caller needs inserted values, such as generated ids, defaults, or timestamps.

```sql
-- name: create_author :one
INSERT INTO authors (name, rating)
VALUES (:name, :rating)
RETURNING *;
```

::: code-group

```python [example.py]
async def create_author(
    self,
    name: str,
    rating: int | None,
) -> Author | None:
    query = """
        INSERT INTO authors (
          name,
          rating
        )
        VALUES
          (%(name)s, %(rating)s)
        RETURNING authors.id AS id, authors.name AS name, authors.rating AS rating
    """

    params = {
        "name": name,
        "rating": rating,
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

## `RETURNING *` and wildcard expansion

`RETURNING *` is expanded during generation, so generated mapping still uses explicit fields.

Return specific columns when the generated API should expose less data:

```sql
-- name: create_author_returning_id :one
INSERT INTO authors (name)
VALUES (:name)
RETURNING id;
```

See [Scalar returns](../reference/annotations#scalar-returns).

