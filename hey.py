from flask import Flask, request, abort, jsonify, make_response, g
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os
import uuid
import time
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set")

logging.debug("DATABASE_URL:", DATABASE_URL)
engine = create_engine(DATABASE_URL.strip())

@app.before_request
def start_timer_for_access_log():
    g.start_time = time.time()

@app.before_request
def authentincation_middleware():
    api_key = request.headers.get('X-API-KEY')
    if not api_key or api_key != 'HelloWorld':
        logging.warning(f"Unauthorized access attempt: {request.remote_addr}")
        response = make_response(jsonify({
            "error": "Unauthorized",
            "message": "Invalid API key"
        }), 401)
        abort(response)

@app.after_request
def set_json_content_type(response):
    response.headers['Content-Type'] = 'application/json'
    return response

@app.after_request
def access_log_middleware(response):
    if hasattr(g, 'start_time'):
        latency_sec = time.time() - g.start_time
        latency_ms = latency_sec * 1000
        logging.info(f"Request: {request.method} {request.path} from {request.remote_addr}, "
                     f"Latency: {latency_ms:.2f} ms")
    return response

@app.route('/status', methods=['GET'])
def status():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1")).fetchone()
            return jsonify({"status": "ok", "message": "ok"}), 200
    except SQLAlchemyError as e:
        response = jsonify({
            "status": "failed",
            "message": str(e)
        })
        response.status_code = 500  
        return response


@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if 'first_name' not in data:
            return '{"error": "Bad Request", "message": "first_name is required"}', 400
        if 'last_name' not in data:
            return '{"error": "Bad Request", "message": "last_name is required"}', 400
        if 'email' not in data:
            return '{"error": "Bad Request", "message": "email is required"}', 400
        if 'password' not in data:
            return '{"error": "Bad Request", "message": "password is required"}', 400
        if not is_valid_email(data['email']):
            return '{"error": "Bad Request", "message": "Invalid email format"}', 400
        if not is_strong_password(data['password']):
            return '{"error": "Bad Request", "message": "Password must be at least 8 characters long, contain at least one uppercase letter and one digit"}', 400


        
        # TODO: Validate email and password complexity - DONE

        with engine.connect() as connection:
            existing_user = connection.execute(
        text("SELECT * FROM users WHERE email = :email"), 
        {'email': data['email']}
    ).fetchone()
        if existing_user:
            return jsonify({"error": "Bad Request", "message": "Email already exists"}), 400



            
            user_id = str(uuid.uuid4())
            result = connection.execute(
                text("INSERT INTO users (id, first_name, last_name, email, password, created_at, updated_at) VALUES (:user_id, :first_name, :last_name, :email, :password, :created_at, :updated_at)"),
                {
                    'user_id': user_id,
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                    'password': data['password'],
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })
            connection.commit()
                
            return jsonify({"id": user_id}), 201

    except SQLAlchemyError as e:
        # TODO: Return a 400 in case we fail on email uniqueness
        return '{"error": "Internal Server Error", "message": "'+ str(e) +'"}', 500

@app.route('/version', methods=['GET'])
def version():
    return '{"version": "0.0.1"}', 200

@app.route('/users', methods=['GET'])
def get_users():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM users"))
            users = [dict(row) for row in result]
            return jsonify(users), 200
    except SQLAlchemyError as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500
    
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def is_strong_password(password):
    
    return (
        len(password) >= 8 and
        any(char.isupper() for char in password) and
        any(char.isdigit() for char in password)
    )



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)