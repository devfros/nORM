-- repo_name: Repo

-- name: basic :many
SELECT * FROM authors
ORDER BY n.ord();

-- name: named :many
SELECT * FROM authors
ORDER BY n.ord(_, :foo, :bar);

-- name: multiple :many
SELECT * FROM authors
ORDER BY n.ord(), n.ord();

-- name: matching_param :many
SELECT * FROM authors
WHERE id = :order_by
ORDER BY n.ord();

-- name: multiple_tables :many
SELECT * FROM authors a
JOIN books b ON b.author_id = a.id
ORDER BY
n.ord(a, :author_order, :author_desc),
n.ord(b, :book_order, :book_desc);
