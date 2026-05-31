-- repo_name: TestRepo

-- name: avg :one
SELECT AVG(a.rating) AS avg_rating
FROM authors a;

-- name: coalesce :one
SELECT COALESCE(a.rating, 0) AS rating_safe FROM authors a;

-- name: count :one
SELECT COUNT(*) AS total_authors FROM authors a;

-- name: count_distinct :one
SELECT COUNT(DISTINCT a.name) AS unique_names
FROM authors a;

-- name: count_without_alias :one
select count(*) from some_table;

-- name: custom_function :one
SELECT custom_score(a.rating) AS score
FROM authors a;

-- name: lower :one
SELECT LOWER(a.name) AS lower_name FROM authors a;

-- name: max :one
SELECT MAX(a.rating) AS max_rating
FROM authors a;

-- name: min :one
SELECT MIN(a.rating) AS min_rating
FROM authors a;

-- name: nested_lower_coalesce :one
SELECT LOWER(COALESCE(a.name, '')) AS canonical_name
FROM authors a;
