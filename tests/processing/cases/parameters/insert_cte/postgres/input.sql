-- repo_name: Repo

-- name: InsertCode :one
WITH cc AS (
            INSERT INTO td3.codes(created_by, updated_by, code, hash, is_private)
            VALUES (:created_by, :created_by, :code, :hash, false)
            RETURNING hash
)
INSERT INTO td3.test_codes(created_by, updated_by, test_id, code_hash)
VALUES(
            :created_by, :created_by, :test_id, (select hash from cc)
)
RETURNING *;
