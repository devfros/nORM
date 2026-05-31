-- repo_name: TestRepo

-- name: main :one
SELECT a.id FROM authors a
WHERE a.name = :_name AND a.rating = :_rating OR
      a.name LIKE :_namelike AND a.rating > :_max_rating;
