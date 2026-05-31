-- repo_name: TestRepo

-- name: UpdateAuthor :one
update authors
set names[:idx] = :name
where id = :id
RETURNING *;
