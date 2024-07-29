FROM python:3.9.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask sqlalchemy psycopg2-binary

EXPOSE 5000

CMD ["python", "hey.py"]
