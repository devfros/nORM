-- repo_name: Repo

-- name: ListUsersByRole :many
SELECT * FROM foo.users WHERE role = :role;
