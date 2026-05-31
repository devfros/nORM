-- repo_name: Repo

-- name: ListExplicitCols :many
SELECT x FROM explicit_cols;

-- name: ListInferredCols :many
SELECT id, name FROM inferred_cols;
