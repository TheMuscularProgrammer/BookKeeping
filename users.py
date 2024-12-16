from flask import Blueprint, request, jsonify
from db import get_db_connection
import bcrypt
import uuid
from datetime import datetime
from sqlalchemy import text

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Validations
    if 'first_name' not in data:
        return jsonify({"error": "Bad Request", "message": "first_name is required"}), 400
    if 'last_name' not in data:
        return jsonify({"error": "Bad Request", "message": "last_name is required"}), 400
    if 'email' not in data:
        return jsonify({"error": "Bad Request", "message": "email is required"}), 400
    if 'password' not in data:
        return jsonify({"error": "Bad Request", "message": "password is required"}), 400
    
    # Hash password
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    # Database connection and user creation
    with get_db_connection() as connection:
        existing_user = connection.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {'email': data['email']}
        ).fetchone()
        
        if existing_user:
            return jsonify({"error": "Bad Request", "message": "Email already exists"}), 400
        
        # Generate new user ID
        user_id = str(uuid.uuid4())
        connection.execute(
            text(
                "INSERT INTO users (id, first_name, last_name, email, password, created_at, updated_at) "
                "VALUES (:user_id, :first_name, :last_name, :email, :password, :created_at, :updated_at)"
            ),
            {
                'user_id': user_id, 
                'first_name': data['first_name'], 
                'last_name': data['last_name'],
                'email': data['email'], 
                'password': hashed_password.decode('utf-8'),
                'created_at': datetime.now(), 
                'updated_at': datetime.now()
            }
        )
        connection.commit()
    
    return jsonify({"id": user_id}), 201
