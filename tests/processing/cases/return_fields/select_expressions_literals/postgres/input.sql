-- repo_name: TestRepo

-- name: literal_int :one
SELECT 42 AS answer FROM authors;

-- name: literal_string :one
SELECT 'hello' AS greeting FROM authors;

-- name: literal_scientific :one
SELECT 1.2e3 AS metric FROM authors;

-- name: null_literal :one
SELECT NULL AS missing_value
FROM authors;

-- name: boolean_literal :one
SELECT TRUE AS is_active FROM authors;

-- name: typed_null_cast :one
SELECT CAST(NULL AS INT) AS maybe_rating
FROM authors a;
