-- repo_name: Repo

-- name: ListAuthors :many
SELECT * FROM authors WHERE foo = :foo;
