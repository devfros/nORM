-- repo_name: TestRepo

-- name: select :one
SELECT
    (SELECT COUNT(*) FROM books b WHERE b.id = :id) AS book_count
FROM authors a;

-- name: correlated_filter :one
SELECT *
FROM authors a
WHERE EXISTS (
  SELECT 1
  FROM books b
  WHERE b.author_id = a.id
    AND a.id = :author_id
);

-- name: complex :one
SELECT * FROM books b WHERE b.author_id = :author_id or b.year in (
  SELECT year FROM books b2 WHERE b2.title LIKE :title
);
