-- repo_name: TestRepo

-- name: unary_plus :one
SELECT +a.rating AS pos_rating
FROM authors a;

-- name: unary_negation :one
SELECT -a.rating AS neg_rating
FROM authors a;

-- name: not_expression :one
SELECT NOT (a.rating > 3) AS not_high
FROM authors a;
