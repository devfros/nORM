-- repo_name: Repo

-- name: AdvisoryLockOne :one
SELECT pg_advisory_lock(:lock);

-- name: AdvisoryUnlock :many
SELECT pg_advisory_unlock(:lock);

-- name: AdvisoryLockExecResult :exec
SELECT pg_advisory_lock(:lock);
