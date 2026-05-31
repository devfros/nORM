from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_sync_connection, open_sync_connection


def main() -> None:
    conn = open_sync_connection()
    try:
        repo = Repo(conn)
        created = repo.create(name="Ada", rating=5)
        assert created is not None
        assert created.name == "Ada"
        assert created.rating == 5

        fetched = repo.get_one(id=created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Ada"

        updated = repo.update_one(name="Augusta", id=created.id, rating=10)
        assert updated is not None
        assert updated.name == "Augusta"
        assert updated.rating == 10

        repo.delete(id=created.id)
        assert repo.get_one(id=created.id) is None
        assert repo.count(id=created.id) == 0
    finally:
        close_sync_connection(conn)


if __name__ == "__main__":
    main()
