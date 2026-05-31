from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_sync_connection, open_sync_connection


def main() -> None:
    conn = open_sync_connection()
    try:
        repo = Repo(conn)
        repo.create(name="Ada", rating=5)

        count = repo.count(id=0)
        assert count == 1

        fetched = repo.get_one(id=0)
        assert fetched is not None
        assert fetched.name == "Ada"

        name = repo.one_column(id=0)
        assert name == "Ada"
    finally:
        close_sync_connection(conn)


if __name__ == "__main__":
    main()
