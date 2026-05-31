-- repo_name: TestRepo

-- name: cast_expression :one
SELECT CAST(a.rating AS TEXT) AS rating_txt FROM authors a;

-- name: cast_array_int :one
SELECT CAST(NULL AS INT[]) AS maybe_ids
FROM authors a;

-- name: cast_array_shorthand :one
SELECT NULL::TEXT[] AS tags_txt
FROM authors a;

-- name: cast_array_varchar :one
SELECT CAST(a.rating AS VARCHAR[]) AS rating_tags
FROM authors a;
