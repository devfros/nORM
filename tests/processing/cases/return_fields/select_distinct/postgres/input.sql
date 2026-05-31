-- repo_name: TestRepo

-- name: distinct_columns :one
SELECT DISTINCT a.name, a.rating
FROM authors a;

-- name: distinct_expression_mix :one
SELECT DISTINCT a.id, LOWER(a.name) AS lower_name
FROM authors a;

-- name: distinct_on_alias :one
SELECT DISTINCT ON (a.id) a.id AS author_id, a.name
FROM authors a
ORDER BY a.id, a.name;
