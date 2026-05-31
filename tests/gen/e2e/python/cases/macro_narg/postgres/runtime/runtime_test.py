from out.repo import Repo

from tests.gen.e2e.python.runtime.connections import close_sync_connection, open_sync_connection


def main() -> None:
    conn = open_sync_connection()
    try:
        repo = Repo(conn)
        by_id = repo.non_nullable_column(1)
        assert by_id is not None
        assert by_id.name == "Ada"

        by_rating = repo.nullable_column(5)
        assert by_rating is not None
        assert by_rating.name == "Ada"
    finally:
        close_sync_connection(conn)


if __name__ == "__main__":
    main()
