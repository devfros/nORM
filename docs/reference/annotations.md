# Query annotations

Every query in a repository file needs a name annotation. A repository file can also declare the generated class name.

## Repository annotation

Place this before the first query in a `*.sql` file:

```sql
-- repo_name: UsersRepo
```

nORM uses that name for the generated repository class.

## Query annotation

Place this immediately before each SQL statement:

```sql
-- name: get_user :one
SELECT * FROM users
WHERE id = :id;
```

Format:

```text
-- name: <query_name> :<command>
```

- `query_name` becomes the generated method name (`get_user` -> `get_user`).
- `command` controls return shape and execution behavior.

## Commands

| Command | Generated behavior (Python) |
| :--- | :--- |
| `:one` | Return at most one row, model, or scalar |
| `:many` | Return a list of rows, models, or scalars |
| `:exec` | Execute without returning row data |
| `:execrows` | Execute and return affected row count (`cur.rowcount`) |
| `:execlastid` | Execute and return last insert id (dialect-specific) |

### `:one`

Use `:one` for single-row reads and `INSERT`/`UPDATE`/`DELETE ... RETURNING` statements where one row is expected.

```sql
-- name: get_author :one
SELECT * FROM authors
WHERE id = :id;
```

Generated signature:

::: code-group

```python
async def get_author(self, id: int) -> Author | None: ...
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

### `:many`

Use `:many` for multi-row reads and `RETURNING` statements where multiple rows are valid.

```sql
-- name: list_authors :many
SELECT * FROM authors;
```

Generated signature:

::: code-group

```python
async def list_authors(self) -> list[Author]: ...
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

### `:exec`

Use `:exec` when callers do not need returned rows.

```sql
-- name: delete_author :exec
DELETE FROM authors
WHERE id = :id;
```

Generated signature:

::: code-group

```python
async def delete_author(self, id: int) -> None: ...
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

### `:execrows`

Use `:execrows` when callers need the number of affected rows.

```sql
-- name: update_many :execrows
UPDATE authors
SET name = :name, rating = :rating
RETURNING *;
```

Generated signature and body:

::: code-group

```python
async def update_many(
    self,
    name: str,
    rating: int | None,
) -> int:
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

### `:execlastid`

Use `:execlastid` for inserts where the caller needs the auto-generated id. Support depends on the target dialect.

```sql
-- name: create_author :execlastid
INSERT INTO authors (name) VALUES (:name);
```

## Scalar returns {#scalar-returns}

When a query returns exactly one column - in `SELECT`, or in `INSERT` / `UPDATE` / `DELETE ... RETURNING` — nORM generates a scalar return type instead of a row model:

```sql
-- name: count_authors :one
SELECT COUNT(*) AS count FROM authors
WHERE id = :id;
```

::: code-group

```python
async def count_authors(self, id: int) -> int | None: ...
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

## Row schemas

When a query does not map to a single table model, nORM generates a `<QueryName>Row` model:

```sql
-- name: list_author_summaries :many
SELECT name, rating FROM authors;
```

::: code-group

```python
class ListAuthorSummariesRow(BaseModel):
    name: str
    rating: int | None

async def list_author_summaries(self) -> list[ListAuthorSummariesRow]: ...
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

## Documenting queries

Lines starting with `--` between the name annotation and the SQL body become method docstrings in generated code.
See [Query comments](../guides/query_comments).

## Related

- [Fetching records](../guides/select)
- [Inserting records](../guides/insert)
- [Updating records](../guides/update)
- [Deleting records](../guides/delete)
- [Macros](./macros)
