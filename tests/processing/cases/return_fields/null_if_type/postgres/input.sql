-- repo_name: TestRepo

-- name: GetRestrictedId :one
SELECT
  NULLIF(id, 1) restricted_id
FROM
  author;
