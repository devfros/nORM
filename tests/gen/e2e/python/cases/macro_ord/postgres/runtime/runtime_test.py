import asyncio

from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_connection, open_connection


async def main() -> None:
    conn = await open_connection()
    try:
        repo = Repo(conn)
        ordered = await repo.basic(order_by="name")
        assert [author.name for author in ordered] == ["Ada", "Bob"]

        named = await repo.named(foo="rating", bar=True)
        assert named[0].name == "Bob"
        assert named[1].name == "Ada"

        joined = await repo.multiple_tables(
            author_order="name",
            book_order="title",
        )
        assert len(joined) == 2
        assert joined[0].name == "Ada"
        assert joined[0].title == "First"
        assert joined[1].name == "Bob"
        assert joined[1].title == "Second"
    finally:
        await close_connection(conn)


if __name__ == "__main__":
    asyncio.run(main())
