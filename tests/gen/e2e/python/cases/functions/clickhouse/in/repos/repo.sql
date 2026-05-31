-- repo_name: Repo

-- name: CallAdd :one
SELECT add(CAST(:a AS Nullable(Int32)), CAST(:b AS Nullable(Int32)));

-- name: CallMul :one
SELECT mul(CAST(:a AS Nullable(Int32)));
