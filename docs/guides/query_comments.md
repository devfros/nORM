# Query comments

Document generated repository methods with SQL comments between the `-- name:` line and the query body.

Those lines become Python docstrings on the generated method. They are separate from `-- name:` and `-- repo_name:` annotations.

## Syntax

```sql
-- name: list_products :many
-- Returns all products in the catalog.
-- Supports pagination at the application layer.
SELECT * FROM products;
```

::: code-group

```python
async def list_products(
    self,
) -> list[Product]:
    """
    Returns all products in the catalog.
    Supports pagination at the application layer.
    """

    query = """
        SELECT
          products.id AS id,
          products.name AS name
        FROM products
    """
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


This works for every query command (`:one`, `:many`, `:exec`, `:execrows`, etc.):

```sql
-- name: create_item :execrows
-- Inserts a product and returns the affected row count.
INSERT INTO products (name) VALUES (:name);
```

::: code-group

```python
async def create_item(
    self,
    name: str,
) -> int:
    """
    Inserts a product and returns the affected row count.
    """
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


## Related

- [Schema comments](./schema_comments) - `COMMENT ON` in DDL
- [Query annotations](../reference/annotations)
