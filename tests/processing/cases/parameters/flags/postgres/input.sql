-- repo_name: TestRepo

-- name: nullable :one
select * from authors a where a.id = n.narg(:id);

-- name: nullable_and_optional :one
select * from authors a where a.id = n.narg(:_id);

-- name: optional :one
select * from authors a where a.id = :_id;
