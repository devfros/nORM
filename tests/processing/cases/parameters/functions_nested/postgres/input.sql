-- repo_name: TestRepo

-- name: abs_round :one
SELECT * FROM authors WHERE ABS(ROUND(:num, 0)) > 5;

-- name: lower_trim :one
SELECT * FROM authors WHERE LOWER(TRIM(:text)) = 'test';
