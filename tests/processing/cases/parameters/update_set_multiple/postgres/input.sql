-- repo_name: TestRepo

-- name: UpdateSetMultiple :exec
UPDATE foo SET (name, slug) = (:name, :slug);
