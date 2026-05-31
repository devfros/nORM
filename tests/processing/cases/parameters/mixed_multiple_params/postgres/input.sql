-- repo_name: TestRepo

-- name: main :one
SELECT * FROM books WHERE author_id = :author_id AND title LIKE :title AND year > :year;
