-- repo_name: TestRepo

-- name: Update :exec
UPDATE testing
SET value = CASE :value WHEN true THEN 'Hello' WHEN false THEN 'Goodbye' ELSE value END;
