-- repo_name: TestRepo

-- name: Lower :many
SELECT bar FROM foo WHERE bar = :bar AND LOWER(bat) = :bat;
