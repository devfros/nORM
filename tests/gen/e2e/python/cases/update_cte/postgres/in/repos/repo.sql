-- repo_name: Repo

-- name: UpdateCode :one
WITH cc AS (
  UPDATE td3.codes
  SET
      created_by = :created_by,
      updated_by  = :created_by,
      code = :code,
      hash = :hash,
      is_private = false
  RETURNING hash
)
UPDATE td3.test_codes
SET
  created_by = :created_by,
  updated_by  = :created_by,
  test_id = :test_id,
  code_hash = cc.hash
  FROM cc
RETURNING *;
