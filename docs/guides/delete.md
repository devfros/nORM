# Deleting records

## Basic delete (`:exec`)

Use `:exec` when the caller only needs rows removed and does not need deleted data back.

```sql
-- name: delete_author :exec
DELETE FROM authors
WHERE id = :id;
```

::: code-group

```python [example.py]
async def delete_author(
    self,
    id: int,
) -> None:
    query = """
        DELETE FROM authors
        WHERE
          id = %(id)s
    """

    params = {
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

## Delete and return deleted rows

Use `RETURNING` when the caller needs the deleted values.

```sql
-- name: delete_author_returning :one
DELETE FROM authors
WHERE id = :id
RETURNING *;
```


Generated mapping expands `RETURNING *` to explicit columns, the same way it handles `SELECT *` and `UPDATE ... RETURNING *`.

## `RETURNING` a single column

```sql
-- name: delete_author_returning_id :one
DELETE FROM authors
WHERE id = :id
RETURNING id;
```

See [Scalar returns](../reference/annotations#scalar-returns).

## Related guides

For runtime-composable delete criteria, see:

- [Dynamic filtering](./dynamic_filtering)
