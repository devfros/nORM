-- repo_name: Repo

-- name: non_dynamic :many
SELECT * FROM authors
GROUP by id, rating
HAVING id = :id or rating > :rating;

-- name: optional_id :many
SELECT * FROM authors
GROUP by id, rating
HAVING id = :_id or rating > :rating;

-- name: optional_rating :many
SELECT * FROM authors
GROUP by id, rating
HAVING id = :id or rating > :_rating;

-- name: full_optional :many
SELECT * FROM authors a
GROUP by a.id, a.rating
HAVING id = :_id or rating > :_rating;

-- name: with_list_macro :many
SELECT * FROM authors
GROUP by id, rating
HAVING id = :_id or rating in (n.list(:_ratings));

-- name: with_narg_macro :many
SELECT * FROM authors
GROUP by id, rating
HAVING id = n.narg(:_id) or rating = :_rating;
