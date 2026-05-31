import asyncio

from out.repo import CreateParams, Repo, UpdateOneParams

from tests.gen.e2e.python.runtime.connections import close_connection, open_connection


async def main() -> None:
    conn = await open_connection()
    try:
        repo = Repo(conn)
        created = await repo.create(CreateParams(name="Ada", rating=5))
        assert created is not None
        assert created.name == "Ada"
        assert created.rating == 5

        fetched = await repo.get_one(id=created.id)
        assert fetched is not None
        assert fetched.id == created.id

        updated = await repo.update_one(
            UpdateOneParams(name="Augusta", rating=10, id=created.id)
        )
        assert updated is not None
        assert updated.name == "Augusta"
        assert updated.rating == 10

        assert await repo.one_column(id=created.id) == "Augusta"

        partials = await repo.partial()
        assert any(row.name == "Augusta" and row.rating == 10 for row in partials)

        await repo.delete(id=created.id)
        assert await repo.get_one(id=created.id) is None
    finally:
        await close_connection(conn)


if __name__ == "__main__":
    asyncio.run(main())
