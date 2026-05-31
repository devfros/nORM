-- repo_name: TestRepo

-- name: LowerSwitchedOrder :many
SELECT bar FROM foo WHERE bar = :bar AND bat = LOWER(:bat);
