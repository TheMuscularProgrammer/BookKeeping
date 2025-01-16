import pytest
import os
from sqlalchemy import create_engine, text

@pytest.fixture(scope="session")
def db_connection():
    """Create in-memory SQLite database for testing"""
    DATABASE_URL = "sqlite:///:memory:"
    os.environ['DATABASE_URL'] = DATABASE_URL
    
    engine = create_engine(DATABASE_URL)
    
    # Create all tables
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """))
        
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                account_number TEXT NOT NULL,
                type TEXT NOT NULL,
                balance_cents INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            )
        """))
        
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                initiator_id TEXT NOT NULL,
                from_bank_account_id TEXT,
                to_bank_account_id TEXT,
                amount INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY(from_bank_account_id) REFERENCES accounts(id),
                FOREIGN KEY(to_bank_account_id) REFERENCES accounts(id)
            )
        """))
    
    # Return a new connection for the tests to use
    return engine.connect()

@pytest.fixture(autouse=True)
def cleanup_database(db_connection):
    """Clean up data after each test"""
    yield
    
    # Clean up tables after test
    with db_connection.begin():
        db_connection.execute(text("DELETE FROM transactions"))
        db_connection.execute(text("DELETE FROM accounts"))
        db_connection.execute(text("DELETE FROM users"))

@pytest.fixture(scope="session")
def base_url():
    """Base URL of the server"""
    return "http://localhost:5001"