import psycopg2

from app.config import settings


def get_connection(
    host=None,
    port=None,
    database=None,
    user=None,
    password=None,
):
    return psycopg2.connect(
        host=host or settings.postgres_host,
        port=port or settings.postgres_port,
        database=database or settings.postgres_db,
        user=user or settings.postgres_user,
        password=password or settings.postgres_password,
    )


def test_connection(
    host,
    port,
    database,
    user,
    password,
):
    connection = get_connection(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

        return version

    finally:
        connection.close()