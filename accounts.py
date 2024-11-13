from flask import Blueprint, request, jsonify
from db import get_db_connection
import uuid

account_bp = Blueprint('account_bp', __name__)

@account_bp.route('/', methods=['POST'])
def create_account():
    data = request.get_json()
    if 'owner_id' not in data:
        return jsonify({"error": "Bad Request", "message": "owner_id is required"}), 400
    
    account_id = str(uuid.uuid4())
    with get_db_connection() as connection:
        connection.execute(
            "INSERT INTO accounts (id, owner_id) VALUES (:account_id, :owner_id)",
            {'account_id': account_id, 'owner_id': data['owner_id']}
        )
        connection.commit()
    
    return jsonify({"id": account_id}), 201
