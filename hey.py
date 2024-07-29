from flask import Flask
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set")
print("DATABASE_URL:", DATABASE_URL)
engine = create_engine(DATABASE_URL.strip())

@app.route('/status', methods=['GET'])
def status():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).fetchone()
            return 'Database connection successful', 200
    except SQLAlchemyError as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
