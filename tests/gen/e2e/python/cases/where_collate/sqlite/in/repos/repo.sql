-- repo_name: Repo

-- name: get_account_by_name :one
SELECT * FROM accounts
WHERE name = :name COLLATE NOCASE
LIMIT 1;
