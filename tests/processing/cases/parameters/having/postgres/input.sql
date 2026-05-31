-- repo_name: Repo

-- name: ColdCities :many
SELECT city
FROM weather
GROUP BY city
HAVING max(temp_lo) < :temp_lo;
