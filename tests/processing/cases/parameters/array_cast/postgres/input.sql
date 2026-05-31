-- repo_name: TestRepo

-- name: array_int :one
SELECT *
FROM authors a
WHERE CAST(:ids AS INT[]) IS NOT NULL;

-- name: array_shorthand :one
SELECT *
FROM authors a
WHERE :tags::TEXT[] IS NOT NULL;

-- name: array_varchar :one
SELECT *
FROM authors a
WHERE CAST(:tags AS VARCHAR[]) IS NOT NULL;
