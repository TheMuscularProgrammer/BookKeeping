from sqlalchemy import create_engine
from contextlib import contextmanager
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set")

# Check if we're running tests (SQLite) or production (PostgreSQL)
is_testing = DATABASE_URL.startswith('sqlite')

# For SQLite, we need to handle foreign keys explicitly
if is_testing:
    engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
    with engine.connect() as conn:
        conn.execute('PRAGMA foreign_keys = ON')
else:
    engine = create_engine(DATABASE_URL.strip())

@contextmanager
def get_db_connection():
    """Context manager for getting DB connection"""
    connection = engine.connect()
    try:
        yield connection
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise
    finally:
        connection.close()