-- repo_name: Repo

-- name: FooByBarB :many
SELECT a, b from foo where foo.a in (select a from bar where bar.b = :b);

-- name: FooByList :many
SELECT a, b from foo where foo.a in (:a1, :a2);

-- name: FooByNotList :many
SELECT a, b from foo where foo.a not in (:a1, :a2);

-- name: FooByParamList :many
SELECT a, b from foo where :a in (foo.a, foo.b);
