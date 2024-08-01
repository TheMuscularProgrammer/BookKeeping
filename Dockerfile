FROM python:3.9.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask sqlalchemy psycopg2-binary

EXPOSE 5001

CMD ["python", "hey.py"]
