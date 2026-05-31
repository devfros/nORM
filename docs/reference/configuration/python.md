# Python configuration

Python generation settings live under:

```yaml
targets:
  - name: default
    gen:
      python:
        asynchronous: true
        models: pydantic
        max_params: 10
```

## `targets[].gen.python`

- Optional in the config schema, but required for Python output.
- Python is the only fully supported generator today.

### `targets[].gen.python.asynchronous`

- Type: boolean
- Default: `true` (in the template created by `norm init`)
- `true` - async repository methods and async drivers (`psycopg`, `aiosqlite`, `asyncmy`, etc.)
- `false` - sync repository methods and sync drivers (`psycopg.Connection`, `sqlite3`, etc.)

#### Async (default)

::: code-group

```python
from psycopg import AsyncConnection as Connection

class Repo:
    def __init__(self, db: Connection) -> None:
        self.db = db

    async def get_author_by_id(self, id: int) -> Author | None:
        async with self.db.cursor() as cur:
            await cur.execute(query, params)
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


#### Sync {#sync}

Set `asynchronous: false` in `norm.yaml`:

```yaml
gen:
  python:
    asynchronous: false
```

Generated code uses a synchronous connection and plain `def` methods:

::: code-group

```python
from psycopg import Connection

class Repo:
    def __init__(self, db: Connection) -> None:
        self.db = db

    def get_one(
        self,
        id: int,
    ) -> Author | None:
        query = """
            SELECT
              authors.id AS id,
              authors.name AS name,
              authors.rating AS rating
            FROM authors
            WHERE
              authors.id = %(id)s
        """

        params = {
            "id": id,
        }

        with self.db.cursor() as cur:
            cur.execute(query, params)
            result = cur.fetchone()
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


Use sync mode when the application already uses blocking database access, such as scripts, sync workers, or legacy stacks. Async mode fits asyncio applications and async pools (`psycopg` async, `aiosqlite`, etc.). Macros, dynamic filters, partial updates, and embeds behave the same in both modes.

### `targets[].gen.python.models`

- Type: string
- Default: `pydantic`
- Supported values:
  - `pydantic` - generates `pydantic.BaseModel` types
  - `dataclasses` - generates `@dataclass` types

Example generated model with `dataclasses`:

::: code-group

```python
from dataclasses import dataclass

@dataclass
class Author:
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


### `targets[].gen.python.max_params`

- Type: integer
- Default: `10` in the template from `norm init` (see [General configuration](./index#what-norm-init-creates))
- Controls when nORM groups query parameters into a generated input model instead of many method arguments.
- Lower values (for example `1`) mean more queries get a single `*Params` model sooner.
- See [Fetching records](../../guides/select#max_params-and-generated-function-signatures).
