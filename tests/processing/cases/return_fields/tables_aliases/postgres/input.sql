-- repo_name: TestRepo

-- name: self_join_columns :one
SELECT a1.id AS first_id, a2.id AS second_id
FROM authors a1
JOIN authors a2 ON a1.id <> a2.id;

-- name: self_join_wildcards :one
SELECT a1.*, a2.*
FROM authors a1
JOIN authors a2 ON a1.id <> a2.id;
