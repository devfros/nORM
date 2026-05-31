# Schema comments

nORM reads documentation from schema DDL and carries it into generated models and enums.

This works with Postgres-style `COMMENT ON` statements and with inline column comments where the dialect supports them.

## `COMMENT ON` (Postgres)

```sql
CREATE SCHEMA foo;

CREATE TYPE foo.mood AS ENUM ('sad', 'ok', 'happy');

CREATE TABLE foo.bar (
  baz foo.mood NOT NULL
);

COMMENT ON TYPE foo.mood IS 'this is the mood type';
COMMENT ON TABLE foo.bar IS 'this is the bar table';
COMMENT ON COLUMN foo.bar.baz IS 'this is the baz column';
```

::: code-group

```python
class Mood(StrEnum):
    """
    this is the mood type
    """

    SAD = "sad"
    OK = "ok"
    HAPPY = "happy"


class Bar(BaseModel):
    """
    this is the bar table
    """

    baz: Mood  # this is the baz column
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


- **Type / table** comments become class docstrings.
- **Column** comments become inline `# ...` on fields (Pydantic and dataclasses).

## Schema pull

`norm schema pull` keeps `COMMENT ON` statements from `pg_dump`, so pulled schemas preserve database documentation without hand-copying comments.

Requirements are the same as [schema pull](../commands/schema): Postgres engine, `pg_dump`, and `sql.migrations.connection`.

## Related

- [Query comments](./query_comments) - docstrings from repository SQL
- [Configuration](../reference/configuration/index)
