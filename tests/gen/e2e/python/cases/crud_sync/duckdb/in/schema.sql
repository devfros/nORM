CREATE SEQUENCE authors_id_seq START 1;
CREATE SEQUENCE books_id_seq START 1;

CREATE TABLE authors (
    id INTEGER DEFAULT nextval('authors_id_seq') PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    rating INTEGER
);

CREATE TABLE books (
    id INTEGER DEFAULT nextval('books_id_seq') PRIMARY KEY,
    author_id INTEGER NOT NULL REFERENCES authors(id),
    isbn TEXT NOT NULL DEFAULT '' UNIQUE,
    book_type TEXT NOT NULL DEFAULT 'FICTION',
    title TEXT NOT NULL DEFAULT '',
    year INTEGER NOT NULL DEFAULT 2000,
    available TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tags TEXT[] NOT NULL DEFAULT []
);
