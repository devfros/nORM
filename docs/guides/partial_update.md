# Partial update

Use partial updates when callers should be able to update only the fields they provide.

In nORM, this is controlled directly in SQL:

- `:field` -> required update parameter
- `:_field` -> patch parameter, applied only when a value is provided

## Basic update (all fields required)

```sql
-- name: update_authors :one
UPDATE authors
SET name = :name, rating = :rating
RETURNING *;
```

::: code-group

```python [example.py]
async def update_authors(
    self,
    name: str,
    rating: int | None,
) -> Author | None:
    query = """
        UPDATE authors SET name = %(name)s, rating = %(rating)s
        RETURNING authors.id AS id, authors.name AS name, authors.rating AS rating
    """

    params = {
        "name": name,
        "rating": rating,
    }

    async with self.db.cursor() as cur:
        await cur.execute(query, params)
        result = await cur.fetchone()
        ...
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

## Partial update (optional fields)

```sql
-- name: patch_author :exec
UPDATE authors
SET name = :_name, rating = :_rating;
```

::: code-group

```python [example.py]
from ._utils.sentinel import UNSET

async def patch_author(
    self,
    name: str = UNSET,
    rating: int | None = UNSET,
) -> None:
    query = """
        UPDATE authors SET name = CASE
          WHEN %(name__is_set)s
          AND NOT CAST(%(name)s AS TEXT) IS NULL
          THEN %(name)s
          ELSE name
        END, rating = CASE
          WHEN %(rating__is_set)s
          THEN %(rating)s
          ELSE rating
        END
    """

    params = {
        "name__is_set": UNSET.to_bool(name),
        "name": UNSET.to_none(name),
        "rating__is_set": UNSET.to_bool(rating),
        "rating": UNSET.to_none(rating),
    }

    # Clear sentinel values
    params = {
        k: v for k, v in params.items() if v is not UNSET
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

## Mixed update (some required, some optional)

```sql
-- name: optional_rating :execrows
UPDATE authors
SET name = :name, rating = :_rating;
```

::: code-group

```python
async def optional_rating(
    self,
    name: str,
    rating: int | None = UNSET,
) -> int:
    query = """
        UPDATE authors SET name = %(name)s, rating = CASE
          WHEN %(rating__is_set)s
          THEN %(rating)s
          ELSE rating
        END
    """
    ...
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


## Optional patch params inside expressions (not supported)

```sql
-- name: update_author_rating_unsupported :exec
UPDATE authors SET
  rating = :_rating * 2
WHERE id = :id;
```


`:_rating` is not treated as a partial-update patch in this form.
Patch behavior only applies when the right side of `SET` is a direct parameter assignment, such as `column = :_param`.

Use a regular parameter in expressions:

```sql
-- name: update_author_rating_doubled :exec
UPDATE authors SET
  rating = :rating * 2
WHERE id = :id;
```


## How generated SQL applies patch params

For each `:_field`, nORM generates an internal `__is_set` flag and conditionally applies the value:

- if field is set -> use new value
- if field is not set -> keep current column value

For non-null columns, generated SQL also checks `NOT CAST(%(name)s AS TEXT) IS NULL` before applying the value. Dialect-specific SQL may vary.

For nullable columns, passing `None` explicitly sets the column to `NULL`.
For non-null columns, `None` is not applied and the existing value is preserved.

## Related guides

- [Updating records](./update)
- [Query annotations](../reference/annotations)
