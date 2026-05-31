-- repo_name: Repo

-- name: CallAdd :one
SELECT add(CAST(:a AS INTEGER), CAST(:b AS INTEGER));

-- name: CallTyped :one
SELECT main.typed(CAST(:x AS INTEGER));
