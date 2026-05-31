-- repo_name: TestRepo

-- name: main :one
SELECT a.id, x.book_count::bigint as book_count
FROM authors a
CROSS JOIN LATERAL (
    SELECT COUNT(*) AS book_count
    FROM books b
    WHERE b.author_id = a.id
) x;
