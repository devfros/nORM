-- repo_name: TestRepo

-- name: basic :one
UPDATE authors SET name = :name, rating = :rating WHERE id = :id;

-- name: patch_nonnull :one
UPDATE authors
SET name = CASE WHEN :flag THEN :name ELSE name END;

-- name: patch_nullable :one
UPDATE authors
SET rating = CASE WHEN :flag and :rating IS NOT NULL THEN :rating ELSE rating END;
