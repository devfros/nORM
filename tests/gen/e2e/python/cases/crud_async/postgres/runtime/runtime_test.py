import asyncio

from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_connection, open_connection


async def main() -> None:
    conn = await open_connection()
    try:
        repo = Repo(conn)
        created = await repo.create(name="Ada", rating=5)
        assert created is not None
        assert created.name == "Ada"
        assert created.rating == 5

        fetched = await repo.get_one(id=created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Ada"

        updated = await repo.update_one(name="Augusta", id=created.id, rating=10)
        assert updated is not None
        assert updated.name == "Augusta"
        assert updated.rating == 10

        await repo.delete(id=created.id)
        assert await repo.get_one(id=created.id) is None
        assert await repo.count(id=created.id) == 0
    finally:
        await close_connection(conn)


if __name__ == "__main__":
    asyncio.run(main())
