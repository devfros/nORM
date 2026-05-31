import asyncio

from out.having_clause import Repo as HavingRepo
from out.where_clause import Repo as WhereRepo

from tests.gen.e2e.python.runtime.connections import close_connection, open_connection


async def main() -> None:
    conn = await open_connection()
    try:
        where = WhereRepo(conn)
        by_id = await where.non_dynamic(id=1, rating=10)
        assert len(by_id) == 1
        assert by_id[0].name == "Ada"

        by_rating = await where.optional_id(rating=3)
        assert {row.name for row in by_rating} == {"Ada", "Bob"}

        having = HavingRepo(conn)
        optional = await having.optional_rating(id=1)
        assert len(optional) == 1
        assert optional[0].name == "Ada"
    finally:
        await close_connection(conn)


if __name__ == "__main__":
    asyncio.run(main())
