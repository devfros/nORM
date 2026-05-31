-- repo_name: Repo

-- name: non_null_column :many
SELECT name FROM authors
WHERE id IN (n.list(:ids));

-- name: null_column :many
SELECT name FROM authors
WHERE rating IN (n.list(:ratings));

-- name: not_in :many
SELECT name FROM authors
WHERE id NOT IN (n.list(:ratings));
