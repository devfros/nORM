import asyncio

from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_connection, open_connection


async def main() -> None:
    conn = await open_connection()
    try:
        repo = Repo(conn)
        rows = await repo.non_null()
        assert len(rows) == 1
        assert rows[0].name == "Ada"
        assert rows[0].book.title == "First Book"

        nullable = await repo.nullable()
        assert len(nullable) == 1
        assert nullable[0].name == "Ada"
        assert nullable[0].book is not None
        assert nullable[0].book.title == "First Book"

        aliased = await repo.aliased()
        assert aliased[0].foo.name == "Ada"
        assert aliased[0].bar is not None
        assert aliased[0].bar.title == "First Book"
    finally:
        await close_connection(conn)


if __name__ == "__main__":
    asyncio.run(main())
