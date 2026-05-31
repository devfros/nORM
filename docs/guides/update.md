# Updating records

## Basic update (`:exec`)

Use `:exec` when the caller does not need updated rows back.

For an update without `RETURNING`:

```sql
-- name: update_author_name :exec
UPDATE authors
SET name = :name
WHERE id = :id;
```

::: code-group

```python [example.py]
async def update_author_name(self, name: str, id: int) -> None:
    query = """
        UPDATE authors SET name = %(name)s
        WHERE
          id = %(id)s
    """

    params = {
        "name": name,
        "id": id,
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

## Update and return the updated row

Use `RETURNING` when the caller needs the updated values.

```sql
-- name: update_one :one
UPDATE authors
SET name = :name, rating = :rating
WHERE id = :id
RETURNING *;
```

::: code-group

```python [example.py]
async def update_one(
    self,
    name: str,
    id: int,
    rating: int | None,
) -> Author | None:
    query = """
        UPDATE authors SET name = %(name)s, rating = %(rating)s
        WHERE
          id = %(id)s
        RETURNING authors.id AS id, authors.name AS name, authors.rating AS rating
    """

    params = {
        "name": name,
        "rating": rating,
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

## Affected row count (`:execrows`)

Use `:execrows` when callers need the affected row count.

```sql
-- name: update_many :execrows
UPDATE authors
SET name = :name, rating = :rating
RETURNING *;
```

::: code-group

```python
async def update_many(
    self,
    name: str,
    rating: int | None,
) -> int:
    ...
    async with self.db.cursor() as cur:
        await cur.execute(query, params)

        result = cur.rowcount

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
-- name: update_author_name_returning_id :one
UPDATE authors
SET name = :name
WHERE id = :id
RETURNING id;
```

See [Scalar returns](../reference/annotations#scalar-returns).

## Related guides

- [Partial update](./partial_update)
- [Dynamic filtering](./dynamic_filtering)
