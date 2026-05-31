-- repo_name: TestRepo

-- name: main :one
SELECT a.id
FROM authors a
WHERE :p = a.id AND :p = a.name;
