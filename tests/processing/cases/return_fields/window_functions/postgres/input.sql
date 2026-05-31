-- repo_name: TestRepo

-- name: count_over_all :one
SELECT
    COUNT(*) OVER () AS total_rows
FROM books b;

-- name: named_window :one
SELECT
    ROW_NUMBER() OVER w AS rn
FROM books b
WINDOW w AS (PARTITION BY b.author_id ORDER BY b.id);

-- name: row_number_partition :one
SELECT
    ROW_NUMBER() OVER (PARTITION BY a.rating ORDER BY a.id) AS rn
FROM authors a;

-- name: sum_running_total :one
SELECT
    SUM(b.year) OVER (ORDER BY b.id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_year
FROM books b;

-- name: sum_with_frame :one
SELECT
    SUM(b.year) OVER (
        PARTITION BY b.author_id
        ORDER BY b.id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_year_sum
FROM books b;

-- name: without_alias :one
SELECT ROW_NUMBER() OVER (ORDER BY b.id)
FROM books b;
