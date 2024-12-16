FROM python:3.9.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    flask \
    sqlalchemy \
    psycopg2-binary \
    bcrypt \
    flask-jwt-extended

EXPOSE 5001

CMD ["python", "server.py"]