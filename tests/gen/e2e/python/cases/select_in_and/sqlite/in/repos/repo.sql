-- repo_name: Repo

-- name: DeleteAuthor :exec
DELETE FROM
  books AS b
WHERE
  b.author NOT IN (
    SELECT
      a.name
    FROM
      authors a
    WHERE
      a.age >= :a_age
  )
  AND b.translator NOT IN (
    SELECT
      t.name
    FROM
      translators t
    WHERE
      t.age >= :t_age
  )
  AND b.year <= :year;
