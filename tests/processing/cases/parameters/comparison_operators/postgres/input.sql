-- repo_name: TestRepo

-- name: gt :one
SELECT * FROM authors WHERE rating > :min_rating;

-- name: gte :one
SELECT *
FROM authors
WHERE rating >= :min_rating;

-- name: lt :one
SELECT *
FROM authors
WHERE rating < :max_rating;

-- name: lte :one
SELECT * FROM authors WHERE rating <= :max_rating;

-- name: neq :one
SELECT * FROM authors WHERE id != :excluded_id;
