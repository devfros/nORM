# Dynamic filtering

Dynamic filtering lets one SQL query support many filter combinations without building SQL strings in application code.

In nORM, you mark a filter as optional by prefixing the parameter name with `_` in SQL:

- `:_param` -> optional predicate input
- `:param` -> required predicate input

The same syntax works in `WHERE` and `HAVING`.

## Why this is useful

Without dynamic filtering, applications often end up with near-duplicate queries or ad hoc SQL string construction.

Dynamic filtering keeps the source query in one place while generating a typed API for the available filters.
With `n` optional filters, one query can represent up to `2^n` valid filter combinations.

## Basic example

```sql
-- name: optional_id :many
SELECT * FROM authors
WHERE id = :_id or rating > :rating;
```

::: code-group

```python [example.py]
from ._utils.dynamic_filter import build_filter_clauses
from ._utils.sentinel import UNSET

async def optional_id(
    self,
    rating: int,
    id: int = UNSET,
) -> list[Author]:
    query = """
        SELECT
          authors.id AS id,
          authors.name AS name,
          authors.rating AS rating
        FROM authors /*FILTER1*/
    """

    params = {
        "id": id,
        "rating": rating,
    }

    # DYNAMIC FILTER
    query = build_filter_clauses(
        query,
        {
          "id": id,
        },
        {
          "/*FILTER1*/": {'clause': 'WHERE', 'tree': {'t': 'OR', 'l': {'p': ['id'], 'v': 'authors.id = %(id)s'}, 'r': {'v': 'authors.rating > %(rating)s'}}},
        }
    )

    # Clear sentinel values
    params = {
        k: v for k, v in params.items() if v is not UNSET
    }

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

## How it works internally

nORM parses the `WHERE` or `HAVING` expression and builds a predicate tree.
Each leaf condition tracks which optional parameters are required before that condition can be included.

At runtime, nORM prunes branches whose required optional parameters were not provided, then rebuilds a valid clause from the remaining tree.

### Tree illustration

For this query:

```sql
-- name: filter_authors_by_name_and_rating :many
SELECT id FROM authors
WHERE name = :_name
  AND (rating = :_rating OR rating > :_max_rating);
```


The logical tree is conceptually:

```text
AND
├── leaf: name = :name            [requires: name]
└── OR (grouped)
    ├── leaf: rating = :rating    [requires: rating]
    └── leaf: rating > :max_rating [requires: max_rating]
```

Example outcomes:

- `name` only -> `WHERE name = :name`
- `rating` + `max_rating` only -> `WHERE (rating = :rating OR rating > :max_rating)`
- all three -> `WHERE name = :name AND (rating = :rating OR rating > :max_rating)`
- none -> no `WHERE` clause

## Combining with macros

Optional filters can be combined with `n.list()` and `n.narg()`:

```sql
-- name: with_list_macro :many
SELECT * FROM authors
WHERE id = :_id OR rating IN (n.list(:_ratings));

-- name: with_narg_macro :many
SELECT * FROM authors
WHERE id = n.narg(:_id) OR rating = :_rating;
```


## Nested predicates and subqueries

Dynamic filtering is evaluated from the top-level `WHERE` or `HAVING` tree.

If a predicate contains a subquery and depends on an optional placeholder inside that subquery, the outer predicate is treated as optional as a whole.

In practice, nORM does not independently preserve inner `WHERE`/`HAVING` fragments when the parent predicate is removed.

## Safety warning

::: warning Be explicit with destructive queries
If all dynamic predicates are optional and none are provided, nORM removes the clause entirely.

For `DELETE` and `UPDATE`, that can affect more rows than intended.

Use at least one required guard predicate, such as tenant, owner, or id scope, when writing destructive queries with dynamic filtering.
:::

## Safe pattern for DELETE/UPDATE

Keep a required boundary first, then add optional filters:

```sql
-- name: delete_author_books :exec
DELETE FROM books
WHERE author_id = :author_id
  AND year < :_before_year;
```


Here, `author_id` is always required, so query scope is never unbounded even when optional filters are absent.

## Related guides

- [Fetching records](./select)
- [Updating records](./update)
- [Deleting records](./delete)
