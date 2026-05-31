-- repo_name: TestRepo

-- name: abs :one
SELECT * FROM authors WHERE ABS(:num) > 5;

-- name: ceil :one
SELECT * FROM authors WHERE CEIL(:num) > 5;

-- name: floor :one
SELECT * FROM authors WHERE FLOOR(:num) < 5;

-- name: mod :one
SELECT * FROM authors WHERE MOD(:num, 2) = 0;

-- name: power :one
SELECT * FROM authors WHERE POWER(:base, 2) > 10;

-- name: round :one
SELECT * FROM authors WHERE ROUND(:num, 2) > 5.0;

-- name: sqrt :one
SELECT * FROM authors WHERE SQRT(:num) > 2;
