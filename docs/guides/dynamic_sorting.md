# Dynamic sorting

Dynamic sorting lets callers choose `ORDER BY` columns at runtime without building raw SQL strings.

Use `n.ord()` inside `ORDER BY` where you would otherwise build sort strings manually.

## Start with one table

For single-table queries, `n.ord()` can infer the sortable table:

```sql
-- name: list_authors_sorted :many
SELECT * FROM authors
ORDER BY n.ord(), a.id ASC;
```

::: code-group

```python [example.py]
async def list_authors_sorted(
    self,
    order_by: Literal['id', 'name', 'rating'],
    desc: bool = False,
) -> list[Author]:
    query = """
        SELECT
          authors.id AS id,
          authors.name AS name,
          authors.rating AS rating
        FROM authors
        ORDER BY
          /*ORDER1*/ NULLS FIRST
    """

    # ORDER BY
    if order_by not in ['id', 'name', 'rating']:
        raise ValueError("Invalid column name '{}'".format(order_by))

    query = query.replace("/*ORDER1*/", "{} {}".format(order_by, 'DESC' if desc else 'ASC'))

    async with self.db.cursor() as cur:
        await cur.execute(query)
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

## Supported `n.ord()` forms

Choose the macro form based on how explicit the query needs to be:

- `n.ord()`
- `n.ord(table_name_or_alias)`
- `n.ord(table_name_or_alias, :order_by, :desc)`
- `n.ord(_, :order_by)`
- `n.ord(_, :order_by, :desc)`

You can also provide custom parameter names:

```sql
-- name: list_authors_by_sort_params :many
SELECT * FROM authors
ORDER BY n.ord(_, :foo, :bar);
```

::: code-group

```python
async def list_authors_by_sort_params(
    self,
    foo: Literal['id', 'name', 'rating'],
    bar: bool = False,
) -> list[Author]: ...
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


Notes:

- If table is omitted (or `_` is used), nORM accepts it only when query has exactly one table
- In multi-table queries, nORM does not infer table for `n.ord()`; pass table name or alias explicitly
- If you use multiple `n.ord()` calls, custom parameter names help keep signatures clear

## Multi-table sorting

When a query has joins, pass the alias or table explicitly:

```sql
-- name: list_authors_and_books_sorted :many
SELECT a.*, b.*
FROM authors a
JOIN books b ON b.author_id = a.id
ORDER BY n.ord(a, :author_sort, :author_desc), n.ord(b, :book_sort, :book_desc);
```


Generated code validates each sort column against the allowed list for that table and replaces `/*ORDER1*/`, `/*ORDER2*/` placeholders at runtime.

## Related guides

- [Fetching records](./select)
- [Macros reference](../reference/macros)
