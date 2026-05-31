-- repo_name: TestRepo

-- name: insert_returning_star :one
INSERT INTO authors (name, rating)
VALUES ('Bob', 1)
RETURNING *;

-- name: update_returning_table_wildcard :one
UPDATE authors a
SET rating = a.rating + 1
WHERE a.id = 1
RETURNING a.*;
