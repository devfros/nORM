-- repo_name: Repo

-- name: GetRepro :one
select * from repro where id = :id limit 1;
