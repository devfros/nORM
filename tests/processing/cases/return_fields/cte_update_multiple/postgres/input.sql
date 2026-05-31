-- repo_name: Repo

-- name: UpdateUserAddressWithAddress :one
WITH t1 AS (
    UPDATE "address" as a
    SET
    address_line = COALESCE(:address_line, address_line),
    region = COALESCE(:region, region),
    city= COALESCE(:city, city)
    WHERE id = COALESCE(:id, id)
    RETURNING a.id, a.address_line, a.region, a.city
   ),
  t2 AS (
    UPDATE "user_address"
    SET
    default_address = COALESCE(:default_address, default_address)
    WHERE
    user_id = COALESCE(:user_id, user_id)
    AND address_id = COALESCE(:address_id, address_id)
    RETURNING user_id, address_id, default_address
	)
SELECT
user_id,
address_id,
default_address,
address_line,
region,
city From t1,t2;
