-- repo_name: Repo

-- name: get_one :one
SELECT * FROM authors
WHERE id = :id;

-- name: get_many :many
SELECT * FROM authors;

-- name: get_with_books :many
SELECT * FROM authors a
JOIN books b ON b.author_id = a.id;

-- name: create :exec
INSERT INTO authors (name, rating)
VALUES (:name, :rating);

-- name: delete :exec
DELETE FROM authors
WHERE id = :id;

-- name: count :one
SELECT COUNT(*) as count FROM authors
WHERE id = :id;

-- name: one_column :one
SELECT name FROM authors
WHERE id = :id;

-- name: partial :many
SELECT name, rating FROM authors;
