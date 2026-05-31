-- repo_name: TestRepo

-- name: CaseStatementBoolean :many
SELECT CASE
  WHEN id = :id THEN true
  ELSE false
END is_one
FROM foo;
