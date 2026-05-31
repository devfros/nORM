import asyncio

from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_connection, open_connection


async def main() -> None:
    conn = await open_connection()
    try:
        repo = Repo(conn)
        by_id = await repo.non_null_column([1, 3])
        assert set(by_id) == {"Ada", "Cara"}

        by_rating = await repo.null_column([5])
        assert set(by_rating) == {"Ada", "Cara"}

        excluded = await repo.not_in([1, 3])
        assert excluded == ["Bob"]
    finally:
        await close_connection(conn)


if __name__ == "__main__":
    asyncio.run(main())
