# What is nORM?

nORM (no ORM) is a SQL-first code generator for teams that want typed data access without moving query design into an ORM.

You write schema and repository SQL. nORM generates typed models and repository methods from those files.

If you like `sqlc`, nORM should feel familiar. It keeps the same SQL-first workflow while adding helpers for dynamic filters, dynamic sorting, model embedding, and patch-style updates.

## Who this is for

nORM is a good fit if you want to:

- keep SQL and query plans visible
- remove repetitive data-mapping code
- expose strongly typed application APIs
- support runtime filtering and sorting without handwritten SQL string assembly

If you prefer building queries through ORM method chains, nORM is probably not the right tool.

## In a nutshell

### 1. Define your schema

```sql [schema.sql]
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name text NOT NULL,
    rating int
);

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    author_id integer NOT NULL REFERENCES authors(id),
    book_type text NOT NULL DEFAULT 'FICTION',
    title text NOT NULL
);
```


### 2. Write repository SQL

```sql [author_repo.sql]
-- repo_name: AuthorRepo

-- name: get_all_authors :many
SELECT * FROM authors
WHERE rating = :rating;
```


### 3. Generate code

```sh
norm generate
```

::: code-group

```python [author_repo.py]
from psycopg import AsyncConnection as Connection
from pydantic import BaseModel
from .models import Author


class AuthorRepo:
    def __init__(self, db: Connection) -> None:
        self.db = db

    async def get_all_authors(
        self,
        rating: int,
    ) -> list[Author]:
        query = """
            SELECT
              authors.id AS id,
              authors.name AS name,
              authors.rating AS rating
            FROM authors
            WHERE
              authors.rating = %(rating)s
        """

        params = {
            "rating": rating,
        }

        async with self.db.cursor() as cur:
            await cur.execute(query, params)
            result = [
                Author(
                    id=item[0],
                    name=item[1],
                    rating=item[2],
                )
                async for item in cur
            ]

        return result
```

```python [models.py]
from pydantic import BaseModel


class Author(BaseModel):
    id: int
    name: str
    rating: int | None
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

### 4. Use the generated API

::: code-group

```python [main.py]
from norm_out.author_repo import AuthorRepo

async def main():
    async with get_db() as db:
        repo = AuthorRepo(db=db)
        many = await repo.get_all_authors(rating=5)
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


## What nORM adds

Beyond basic SQL-to-code generation, nORM includes features that are awkward to maintain by hand:

- dynamic filtering and sorting macros with validation
- partial updates through `:_field` patch semantics
- model embedding for joins, including nullable embeds through `n.nembed()` for `LEFT JOIN`
- one named-parameter style across supported dialects

## Keep going from here

- [Install nORM](./installing)
- [Getting started with Python](../tutorials/python)
- [Fetching records](../guides/select)
