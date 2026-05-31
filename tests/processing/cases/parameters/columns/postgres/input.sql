-- repo_name: TestRepo

-- name: direct :one
SELECT * FROM authors WHERE id = :id;

-- name: nullability :one
SELECT * FROM authors WHERE rating = :rating AND name = :name;

-- name: text :one
SELECT * FROM authors WHERE name = :name;
