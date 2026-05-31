-- repo_name: TestRepo

-- name: basic :one
UPDATE authors a
SET rating = rating + 1
WHERE a.id = 1
RETURNING a.id, a.rating;

-- name: expression_without_alias :one
UPDATE authors a
SET rating = a.rating + 1
RETURNING a.rating + 1;

-- name: no_returning :one
UPDATE authors
SET rating = rating + 1
WHERE id = 1;
