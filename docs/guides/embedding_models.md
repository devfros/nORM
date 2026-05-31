# Embedding models

Embedding models lets join queries return nested typed objects instead of one flat row with duplicate column names.

Use:

- `n.embed(alias)` for required embedded models
- `n.nembed(alias)` for nullable embedded models (mostly for `LEFT JOIN`)
- `n.embed(alias) AS field_name` / `n.nembed(alias) AS field_name` for custom property names

## Why embed?

Without embedding, joined rows are flat.

```sql
-- name: list_authors_join_books_flat :many
SELECT * FROM authors a
JOIN books b ON b.author_id = a.id;
```


The generated shape is flat (`id`, `id_2`, `author_id`, etc.) because joined tables can have overlapping column names.

With embedding, related columns are grouped into model fields.

## `n.embed()` (required model)

```sql
-- name: list_authors_with_books :many
SELECT
  n.embed(a), n.nembed(b)
FROM authors a
LEFT JOIN books b ON b.author_id = a.id;
```

::: code-group

```python [models.py]
class ListAuthorsWithBooksRow(BaseModel):
    author: Author
    book: Book | None = None
```

```python [mapping.py]
ListAuthorsWithBooksRow(
    author=Author(
        id=item[0],
        name=item[1],
        rating=item[2],
    ),
    book=Book(
        id=item[3],
        author_id=item[4],
        isbn=item[5],
        book_type=item[6],
        title=item[7],
        year=item[8],
        available=item[9],
        tags=item[10],
    ) if not all(v is None for v in item[3:11]) else None,
)
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


## Mix embedded and flat columns

```sql
-- name: list_authors_with_embedded_book :many
SELECT
  a.*, n.embed(b)
FROM authors a
JOIN books b ON b.author_id = a.id;
```


This keeps the flat `authors` columns and adds one nested `book` field.

## Custom field names (`AS`)

By default, embed fields use the singular table name (`authors` -> `author`). Use SQL `AS` to choose a different field name:

```sql
-- name: list_authors_custom_embed_names :many
SELECT
  n.embed(a) AS author_profile, n.nembed(b) AS latest_book
FROM authors a
LEFT JOIN books b ON b.author_id = a.id;
```

::: code-group

```python [models.py]
class ListAuthorsCustomEmbedNamesRow(BaseModel):
    author_profile: Author
    latest_book: Book | None = None
```

```python [mapping.py]
ListAuthorsCustomEmbedNamesRow(
    author_profile=Author(
        id=item[0],
        name=item[1],
        rating=item[2],
    ),
    latest_book=Book(
        id=item[3],
        author_id=item[4],
        isbn=item[5],
        book_type=item[6],
        title=item[7],
        year=item[8],
        available=item[9],
        tags=item[10],
    ) if not all(v is None for v in item[3:11]) else None,
)
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


## `n.nembed()` (nullable model for left joins)

Use `n.nembed()` when the joined table may be absent, most often with `LEFT JOIN`.

```sql
-- name: list_authors_with_optional_book :many
SELECT
  a.*, n.nembed(b)
FROM authors a
LEFT JOIN books b ON b.author_id = a.id;
```

::: code-group

```python [mapping.py]
book=Book(...) if not all(v is None for v in item[3:11]) else None,
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


At runtime, nORM sets `book = None` when all selected columns for that embed block are `NULL`.

## Rules and validation

- `n.embed()` / `n.nembed()` are valid in `SELECT` projection
- argument must be a real table name or alias from `FROM` / `JOIN`
- unknown alias/table is rejected during generation
- `AS` must be a simple identifier for the generated row field name

For generated schema shape:

- every `n.embed(alias)` becomes one nested field (default name from table, or your `AS` name)
- every `n.nembed(alias)` becomes a nullable nested field
- nORM expands embedded columns in SQL projection, then maps result indexes back into nested models

## Related guides

- [Fetching records](./select)
- [Dynamic sorting](./dynamic_sorting)
- [Macros reference](../reference/macros)
