-- repo_name: TestRepo

-- name: GetRestrictedId :one
SELECT
  NULLIF(id, :id) restricted_id
FROM
  author;
