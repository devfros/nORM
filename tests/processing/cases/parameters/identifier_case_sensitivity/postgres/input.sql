-- repo_name: Repo

-- name: GetAuthor :one
SELECT * FROM Authors
WHERE ID = :id LIMIT 1;

-- name: ListAuthors :many
SELECT * FROM Authors
ORDER BY Name;

-- name: CreateAuthor :exec
INSERT INTO Authors (
  Name, Bio
) VALUES (
  :name, :bio
);

-- name: DeleteAuthor :exec
DELETE FROM Authors
WHERE ID = :id;
