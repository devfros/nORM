CREATE SCHEMA app;

CREATE FUNCTION app.foo(bar text) RETURNS bool LANGUAGE sql AS $$ SELECT true $$;
CREATE FUNCTION app.foo(bar integer) RETURNS text LANGUAGE sql AS $$ SELECT 'baz' $$;
CREATE FUNCTION app.add(a int, b int) RETURNS int LANGUAGE sql AS $$ SELECT a + b $$;
CREATE FUNCTION app.returns_table(x int) RETURNS TABLE(id int, name text) LANGUAGE sql AS $$ SELECT 1, 'a' $$;
