-- repo_name: TestRepo

-- name: FindByAddress :one
SELECT * FROM "user" WHERE "metadata"->>'address1' = :metadata LIMIT 1;
