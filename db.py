from sqlalchemy import create_engine
from contextlib import contextmanager
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL.strip())

@contextmanager
def get_db_connection():
    """Context manager for getting DB connection"""
    connection = engine.connect()
    transaction = connection.begin()
    try:
        yield connection
        transaction.commit()
    except:
        transaction.rollback()
        raise
    finally:
        connection.close()