-- repo_name: Repo

-- name: ListExplicitCols :many
SELECT x FROM app.explicit_cols;

-- name: ListInferredCols :many
SELECT id, name FROM app.inferred_cols;

-- name: ListMaterialized :many
SELECT id FROM app.mv;
