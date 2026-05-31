-- repo_name: Repo

-- name: SchemaScopedUpdate :exec
UPDATE foo.bar SET name = :name WHERE id = :id;
