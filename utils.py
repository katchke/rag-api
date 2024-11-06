import os


def create_conn_string() -> str:
    return (
        "postgresql://"
        "%(POSTGRES_USER)s:%(POSTGRES_PASSWORD)s"
        "@%(POSTGRES_HOST)s:%(POSTGRES_PORT)s/"
        "%(POSTGRES_DB)s"
    ) % {
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST"),
        "POSTGRES_PORT": 5432,
        "POSTGRES_DB": os.getenv("POSTGRES_DB"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    }
