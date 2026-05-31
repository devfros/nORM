-- repo_name: TestRepo

-- name: no_dynamic :one
SELECT a.id FROM authors a WHERE a.id = :id;

-- name: single_optional :one
SELECT a.id FROM authors a WHERE a.id = :id OR a.rating > :_rating;

-- name: not :one
SELECT a.id FROM authors a WHERE NOT a.id = :_id OR a.name = :_name;

-- name: parenthesis :one
SELECT a.id FROM authors a
WHERE a.name = :_name AND (a.rating = :_rating OR a.rating > :_max_rating);

-- name: having :one
SELECT a.id, COUNT(b.id) AS book_count
FROM authors a
JOIN books b ON b.author_id = a.id
GROUP BY a.id
HAVING COUNT(b.id) >= :_min_books AND MAX(a.rating) > :_min_rating;
