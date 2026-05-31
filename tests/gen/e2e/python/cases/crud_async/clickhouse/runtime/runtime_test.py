import asyncio

from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_connection, open_connection


async def main() -> None:
    conn = await open_connection()
    try:
        repo = Repo(conn)
        await repo.create(name="Ada", rating=5)

        count = await repo.count(id=0)
        assert count == 1

        fetched = await repo.get_one(id=0)
        assert fetched is not None
        assert fetched.name == "Ada"

        name = await repo.one_column(id=0)
        assert name == "Ada"
    finally:
        await close_connection(conn)


if __name__ == "__main__":
    asyncio.run(main())
