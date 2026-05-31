-- repo_name: TestRepo

-- name: comments_whitespace :one
SELECT
    a.id, -- inline comment
    a.name
FROM authors a;

-- name: placeholders_expression :one
SELECT (a.rating > :min_rating) AS above_min
FROM authors a;
