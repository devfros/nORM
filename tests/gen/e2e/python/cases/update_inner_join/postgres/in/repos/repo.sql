-- repo_name: Repo

-- name: update_x_with_y :exec
UPDATE x INNER JOIN y ON y.a = x.a SET x.b = y.b;
