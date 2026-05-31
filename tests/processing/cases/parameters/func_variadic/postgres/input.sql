-- repo_name: Repo

-- name: UpdateJ :exec
UPDATE
    test
SET
    j = jsonb_build_object(:a::text, :b::text, :c::text, :d::text)
WHERE
    id = :id;
