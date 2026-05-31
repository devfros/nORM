-- repo_name: TestRepo

-- name: concat :one
SELECT * FROM authors WHERE CONCAT(:first, :last) = 'foobar';

-- name: length :one
SELECT * FROM authors WHERE LENGTH(:text) > 5;

-- name: lower :one
SELECT * FROM authors WHERE LOWER(:text) = 'test';

-- name: replace :one
SELECT * FROM authors WHERE REPLACE(:text, 'a', 'b') = 'test';

-- name: substring :one
SELECT * FROM authors WHERE SUBSTRING(:text, 1, 3) = 'foo';

-- name: trim :one
SELECT * FROM authors WHERE TRIM(:text) = 'test';

-- name: upper :one
SELECT * FROM authors WHERE UPPER(:text) = 'TEST';
