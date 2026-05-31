-- repo_name: Repo

-- name: UpsertAuthor :exec
INSERT INTO authors (name, bio)
VALUES (:name, :bio)
ON CONFLICT (name) DO UPDATE
SET bio = :bio;
