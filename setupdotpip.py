from sqlalchemy import create_engine, text

def execute_sql_file(db_url, sql_file_path):
    # Create a database engine using the provided database URL
    engine = create_engine(db_url.strip())
    # Establish a connection
    with engine.connect() as connection:
        try:
            # Read the SQL file
            with open(sql_file_path, 'r') as sql_file:
                sql_script = sql_file.read()

            # Execute the SQL script
            connection.execute(text(sql_script))
            print("SQL script executed successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")

# Example usage
if __name__ == "__main__":
    # Database URL for your engine (SQLite example)
    db_url = "postgresql://postgres:example@localhost:5432/mydatabase"  # Example: "sqlite:///example.db", "postgresql://user:password@localhost/dbname"
    sql_file_path = "tables.sql"  # Path to your SQL file

    execute_sql_file(db_url, sql_file_path)