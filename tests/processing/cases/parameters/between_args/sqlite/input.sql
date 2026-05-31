-- repo_name: Repo

-- name: GetBetweenPrices :many
SELECT  *
FROM    products
WHERE   price BETWEEN :low AND :high;

-- name: GetBetweenPricesTable :many
SELECT  *
FROM    products
WHERE   products.price BETWEEN :low AND :high;

-- name: GetBetweenPricesTableAlias :many
SELECT  *
FROM    products as p
WHERE   p.price BETWEEN :low AND :high;
