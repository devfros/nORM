import asyncio

from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_connection, open_connection


async def _read(conn) -> tuple[str, int | None]:
    async with conn.cursor() as cur:
        await cur.execute("SELECT name, rating FROM authors ORDER BY id LIMIT 1")
        row = await cur.fetchone()
    assert row is not None
    return row[0], row[1]


async def main() -> None:
    conn = await open_connection()
    try:
        repo = Repo(conn)
        assert await _read(conn) == ("Ada", 5)

        await repo.optional_name(rating=20)
        assert await _read(conn) == ("Ada", 20)

        await repo.optional_rating(name="Augusta")
        assert await _read(conn) == ("Augusta", 20)

        await repo.full_optional(rating=99)
        assert await _read(conn) == ("Augusta", 99)
    finally:
        await close_connection(conn)


if __name__ == "__main__":
    asyncio.run(main())
