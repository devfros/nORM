-- repo_name: TestRepo

-- name: group_by_aggregate :one
SELECT a.id, COUNT(*) AS book_count
FROM authors a
JOIN books b ON b.author_id = a.id
GROUP BY a.id;

-- name: having_aggregate_filter :one
SELECT a.id, COUNT(*) AS book_count
FROM authors a
JOIN books b ON b.author_id = a.id
GROUP BY a.id
HAVING COUNT(*) > 1;

-- name: order_by_alias :one
SELECT a.name AS author_name
FROM authors a
ORDER BY author_name;

-- name: order_by_ordinal :one
SELECT a.name
FROM authors a
ORDER BY 1;
