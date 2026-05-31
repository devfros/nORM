CREATE SCHEMA app;

CREATE TABLE app.users (id int, name text);

CREATE VIEW app.explicit_cols(x) AS SELECT 1 AS x;
CREATE VIEW app.inferred_cols AS SELECT id, name FROM app.users;
CREATE MATERIALIZED VIEW app.mv AS SELECT id FROM app.users;
