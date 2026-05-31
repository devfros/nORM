# Macros

nORM macros are SQL helpers you call as `n.<macro>(...)` inside queries.

They keep repository files in SQL while giving nORM enough structure to generate stronger types and safer runtime behavior.
Macros are SQL-compatible expressions, so they do not require a separate query DSL.

## Available macros

| Macro | Purpose | Typical place |
| :--- | :--- | :--- |
| `n.narg(:param)` | Mark argument as nullable | `WHERE`, expressions |
| `n.list(:param)` | Expand list argument for `IN (...)` style filters | `WHERE` |
| `n.ord(...)` | Dynamic `ORDER BY` with validated columns | `ORDER BY` |
| `n.embed(alias)` | Embed joined table as required nested model | `SELECT` |
| `n.embed(alias) AS name` | Same, with custom field name on the row model | `SELECT` |
| `n.nembed(alias)` | Embed joined table as nullable nested model | `SELECT` (usually with `LEFT JOIN`) |
| `n.nembed(alias) AS name` | Same, with custom nullable field name | `SELECT` |

## `n.narg(:param)`

Use `n.narg()` when a parameter should be treated as nullable explicitly.

```sql
-- name: get_author_nullable_id :many
SELECT * FROM authors a
WHERE a.id = n.narg(:id);
```


The generated parameter is nullable in code for the selected target language.

Related guide: [Fetching records](../guides/select#nullable-arguments-with-nnarg).

## `n.list(:param)`

Use `n.list()` when one logical parameter represents multiple values.

```sql
-- name: list_authors_by_ids :many
SELECT * FROM authors
WHERE id IN (n.list(:ids));
```


This is especially useful on dialects that do not support array-style bindings directly.

Related guide: [Fetching records](../guides/select#list-arguments-with-nlist).

## `n.ord(...)`

Use `n.ord()` in `ORDER BY` when the sort column is chosen at runtime.

Supported forms:

- `n.ord()`
- `n.ord(table_name_or_alias)`
- `n.ord(table_name_or_alias, :order_by, :desc)`
- `n.ord(_, :order_by)`
- `n.ord(_, :order_by, :desc)`

Example:

```sql
-- name: list_authors :many
SELECT *
FROM authors a
ORDER BY n.ord(a, :author_sort, :author_desc), a.id ASC;
```


Notes:

- `n.ord()` without table works only when query has exactly one table.
- In multi-table queries, table/alias must be explicit.
- `:order_by` values are validated against real columns on the selected table.

Related guide: [Dynamic sorting](../guides/dynamic_sorting).

## `n.embed(alias)`

Use `n.embed()` to map columns from a joined table into a required nested model.

```sql
-- name: get_authors_with_books :many
SELECT n.embed(a), n.embed(b)
FROM authors a
JOIN books b ON b.author_id = a.id;
```


The generated row shape is nested, such as `author` and `book` objects, instead of flat duplicate-column output.

Without `AS`, field names are derived from the table name in singular form (`authors` -> `author`).

### Custom embed field names

Use SQL `AS` to choose the field name on the generated row model:

```sql
-- name: list_authors_custom_embed_names :many
SELECT n.embed(a) AS author_profile, n.nembed(b) AS latest_book
FROM authors a
LEFT JOIN books b ON b.author_id = a.id;
```


Generated row schema:

::: code-group

```python
class ListAuthorsCustomEmbedNamesRow(BaseModel):
    author_profile: Author
    latest_book: Book | None = None
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


## `n.nembed(alias)`

`n.nembed()` works like `n.embed()`, but the generated nested model is nullable for optional joins.

```sql
-- name: get_authors_with_books_left_join :many
SELECT n.embed(a), n.nembed(b)
FROM authors a
LEFT JOIN books b ON b.author_id = a.id;
```


Generated row shape uses a nullable nested model for the joined table.
At runtime, nORM sets that nested value to null when all columns for that embedded block are `NULL`.

Related guide: [Embedding models](../guides/embedding_models).

## Validation rules

nORM validates macro usage during generation:

- unknown macro name is rejected
- wrong parameter type/count is rejected (for example, `n.list()` without placeholder)
- unknown table/alias in `n.embed`, `n.nembed`, `n.ord` is rejected
- `n.ord(...)` outside `ORDER BY` is rejected
- embed macros outside `SELECT` projection are rejected
- `AS` on embed macros must be a simple identifier (custom row field name)
