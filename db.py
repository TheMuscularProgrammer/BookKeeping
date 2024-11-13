from sqlalchemy import create_engine
from contextlib import contextmanager
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL.strip())

# Context manager for getting DB connection
@contextmanager
def get_db_connection():
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()
