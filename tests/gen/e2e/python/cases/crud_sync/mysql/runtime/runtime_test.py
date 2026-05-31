from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_sync_connection, open_sync_connection


def main() -> None:
    conn = open_sync_connection()
    try:
        repo = Repo(conn)
        repo.create(name="Ada", rating=5)

        fetched = repo.get_one(id=1)
        assert fetched is not None
        assert fetched.name == "Ada"

        repo.update_one(name="Augusta", id=1, rating=10)
        fetched = repo.get_one(id=1)
        assert fetched is not None
        assert fetched.rating == 10

        repo.delete(id=1)
        assert repo.get_one(id=1) is None

    finally:
        close_sync_connection(conn)


if __name__ == "__main__":
    main()
