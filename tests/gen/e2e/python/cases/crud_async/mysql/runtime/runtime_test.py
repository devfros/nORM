import asyncio

from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_connection, open_connection


async def main() -> None:
    conn = await open_connection()
    try:
        repo = Repo(conn)
        await repo.create(name="Ada", rating=5)

        fetched = await repo.get_one(id=1)
        assert fetched is not None
        assert fetched.name == "Ada"

        await repo.update_one(name="Augusta", id=1, rating=10)
        fetched = await repo.get_one(id=1)
        assert fetched is not None
        assert fetched.rating == 10

        await repo.delete(id=1)
        assert await repo.get_one(id=1) is None
    finally:
        await close_connection(conn)


if __name__ == "__main__":
    asyncio.run(main())
