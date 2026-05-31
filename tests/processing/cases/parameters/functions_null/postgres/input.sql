-- repo_name: TestRepo

-- name: coalesce :one
SELECT * FROM authors WHERE COALESCE(:val, 0) > rating;

-- name: nullif :one
SELECT * FROM authors WHERE NULLIF(:val, 0) IS NOT NULL;
