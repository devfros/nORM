-- repo_name: Repo

-- name: InsertValues :exec
INSERT INTO foo (a, b) VALUES (:a, :b);

-- name: InsertMultipleValues :exec
INSERT INTO foo (a, b) VALUES (:a, :b), (:c, :d);
