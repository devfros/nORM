-- repo_name: Repo

-- name: Subquery :many
SELECT
	a,
	name,
	(SELECT alias FROM bar WHERE bar.a=foo.a AND alias = :alias ORDER BY bar.a DESC limit 1) as alias
FROM FOO WHERE a = :a;
