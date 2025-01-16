from sqlalchemy import create_engine
from contextlib import contextmanager
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set")

# Check if we're running with SQLite
is_sqlite = DATABASE_URL.startswith('sqlite')

if is_sqlite:
    engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
    # Enable foreign keys for SQLite
    with engine.connect() as connection:
        connection.execute('PRAGMA foreign_keys = ON')
else:
    engine = create_engine(DATABASE_URL.strip())

@contextmanager
def get_db_connection():
    """Context manager for getting DB connection"""
    connection = engine.connect()
    try:
        if is_sqlite:
            # For SQLite, we need to handle transactions explicitly
            with connection.begin():
                yield connection
        else:
            # For PostgreSQL, keep original behavior
            yield connection
            connection.commit()
    except Exception as e:
        if not is_sqlite:  # Only rollback for PostgreSQL
            connection.rollback()
        raise
    finally:
        connection.close()