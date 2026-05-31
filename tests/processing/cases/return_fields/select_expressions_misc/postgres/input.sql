-- repo_name: TestRepo

-- name: case_expression :one
SELECT CASE WHEN a.rating > 10 THEN 'high' ELSE 'low' END AS rating_band FROM authors a;

-- name: comparison_projection :one
SELECT (a.rating > 3) AS is_high
FROM authors a;

-- name: datetime_interval_add :one
SELECT (b.available + INTERVAL '1 day') AS available_plus_day
FROM books b;

-- name: expression_without_alias :one
SELECT a.rating + 1
FROM authors a;

-- name: logical_projection :one
SELECT (a.rating > 3 AND a.name <> '') AS is_visible
FROM authors a;

-- name: mixed_numeric_coercion :one
SELECT (a.rating + CAST(1.5 AS FLOAT)) AS mixed_num
FROM authors a;

-- name: string_concat :one
SELECT (a.name || '-' || a.id) AS label
FROM authors a;
