-- repo_name: TestRepo

-- name: over_function :one
SELECT a.id
FROM authors a
WHERE LOWER(CAST(:p AS INT)) = '1';

-- name: over_hard :one
SELECT a.id
FROM authors a
WHERE :p::text = a.id;
