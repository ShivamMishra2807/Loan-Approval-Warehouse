import psycopg
from ln.config import DSN
def connect():
    if not DSN:
        raise RuntimeError("LN_DSN is missing. Copy .env.example to .env and configure PostgreSQL.")
    return psycopg.connect(DSN)
