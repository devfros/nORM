-- repo_name: TestRepo

-- name: arithmetic_div :one
SELECT a.rating / 2 AS rating_half
FROM authors a;

-- name: arithmetic_double :one
SELECT a.rating + 0.5 AS next_rating FROM authors a;

-- name: arithmetic_int :one
SELECT a.rating + 1 AS next_rating FROM authors a;

-- name: arithmetic_mod :one
SELECT a.rating % 2 AS rating_mod_two
FROM authors a;

-- name: arithmetic_mul :one
SELECT a.rating * 2 AS rating_times_two
FROM authors a;

-- name: arithmetic_sub :one
SELECT a.rating - 1 AS rating_minus_one
FROM authors a;
