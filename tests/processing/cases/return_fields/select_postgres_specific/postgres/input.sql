-- repo_name: TestRepo

-- name: any_operator_flag :one
SELECT 'fiction' = ANY(b.tags) AS has_fiction
FROM books b;

-- name: array_subscript :one
SELECT b.tags[1] AS first_tag
FROM books b;

-- name: at_time_zone :one
SELECT b.available AT TIME ZONE 'UTC' AS available_utc
FROM books b;
