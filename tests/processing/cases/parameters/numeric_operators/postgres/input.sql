-- repo_name: TestRepo

-- name: between :one
SELECT * FROM authors a WHERE :num BETWEEN 1 AND 2.5;

-- name: between_nullable_bound :one
SELECT a.id
FROM authors a
WHERE :p BETWEEN a.rating AND 10;

-- name: cast :one
SELECT * FROM authors a WHERE :num::numeric > a.rating;

-- name: divide :one
SELECT * FROM authors WHERE rating = :rating / 2;

-- name: equal :one
SELECT * FROM authors a WHERE :num = (1 + 0.5);

-- name: in :one
SELECT * FROM authors a WHERE :num BETWEEN 1 AND 2.5;

-- name: modulo :one
SELECT * FROM authors WHERE rating = :rating % 2;

-- name: multiply :one
SELECT * FROM authors WHERE rating = :rating * 2;

-- name: nested :one
SELECT * FROM authors a WHERE :num = ((1 + 0.5) + 2);

-- name: scientific :one
SELECT * FROM authors a WHERE :num = 1e2;

-- name: subtract :one
SELECT * FROM authors WHERE rating = :rating - 1;
