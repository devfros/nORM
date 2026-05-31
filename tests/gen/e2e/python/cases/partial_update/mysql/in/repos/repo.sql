-- repo_name: Repo

-- name: non_dynamic :execlastid
UPDATE authors
SET name = :name, rating = :rating;

-- name: optional_name :execrows
UPDATE authors
SET name = :_name, rating = :rating;

-- name: optional_rating :execrows
UPDATE authors
SET name = :name, rating = :_rating;

-- name: full_optional :exec
UPDATE authors
SET name = :_name, rating = :_rating;
