-- repo_name: TestRepo

-- name: basic :one
DELETE FROM authors a
WHERE a.id = 1
RETURNING a.id, a.name;

-- name: no_returning :one
DELETE FROM authors
WHERE id = 1;

-- name: returning_star :one
DELETE FROM authors a
WHERE a.id = 1
RETURNING *;
