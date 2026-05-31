-- repo_name: TestRepo

-- name: Any :many
SELECT id
FROM bar
WHERE id = ANY(:ids::bigint[]);
