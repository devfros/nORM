-- repo_name: TestRepo

-- name: main :one
SELECT a.id
FROM authors a
JOIN books b ON b.id = a.id
WHERE :ambiguous = id;
