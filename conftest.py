import os
import psycopg2
import pytest
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "dbname":   os.getenv("DB_NAME", "eshop_test"),
}


@pytest.fixture(scope="session")
def db_setup():
    """Spustí init_db.sql jednou na začátku testovací session."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    with conn.cursor() as cur:
        with open(
            os.path.join(os.path.dirname(__file__), "init_db.sql"), "r"
        ) as f:
            cur.execute(f.read())
    conn.close()


@pytest.fixture()
def db(db_setup):
    """Každý test dostane vlastní spojení v transakci.

    Po skončení testu se provede ROLLBACK — seed data zůstanou nedotčená.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()
