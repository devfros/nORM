CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name text NOT NULL DEFAULT '',
    rating int
);

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    author_id integer NOT NULL REFERENCES authors(id),
    isbn text NOT NULL DEFAULT '' UNIQUE,
    book_type text NOT NULL DEFAULT 'FICTION',
    title text NOT NULL DEFAULT '',
    year integer NOT NULL DEFAULT 2000,
    available timestamp with time zone NOT NULL DEFAULT NOW(),
    tags varchar[] NOT NULL DEFAULT '{}'
);
