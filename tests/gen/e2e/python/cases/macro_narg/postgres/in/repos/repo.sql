-- repo_name: Repo

-- name: non_nullable_column :one
SELECT * FROM authors
WHERE id = n.narg(:id);

-- name: nullable_column :one
SELECT * FROM authors
WHERE rating = n.narg(:rating);
