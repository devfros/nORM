-- repo_name: Repo

-- name: non_dynamic :one
UPDATE authors
SET name = :name, rating = :rating
RETURNING *;

-- name: optional_name :exec
UPDATE authors
SET name = :_name, rating = :rating;

-- name: optional_rating :exec
UPDATE authors
SET name = :name, rating = :_rating;

-- name: full_optional :exec
UPDATE authors
SET name = :_name, rating = :_rating;
