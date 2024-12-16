from flask import Blueprint, request, jsonify
from db import get_db_connection
import uuid
from sqlalchemy import text
from datetime import datetime

account_bp = Blueprint('account_bp', __name__)

@account_bp.route('/', methods=['POST'])
def create_account():
    data = request.get_json()
    if 'owner_id' not in data:
        return jsonify({"error": "Bad Request", "message": "owner_id is required"}), 400
    
    account_id = str(uuid.uuid4())
    account_number = str(uuid.uuid4())  # יצירת מספר חשבון ייחודי
    
    with get_db_connection() as connection:
        connection.execute(
            text(
                "INSERT INTO accounts (id, owner_id, account_number, type, balance_cents, created_at, updated_at) "
                "VALUES (:account_id, :owner_id, :account_number, :type, :balance_cents, :created_at, :updated_at)"
            ),
            {
                'account_id': account_id, 
                'owner_id': data['owner_id'],
                'account_number': account_number,
                'type': data.get('type', 'checking'),  # ברירת מחדל לחשבון עו"ש
                'balance_cents': data.get('balance_cents', 0),  # יתרת פתיחה 0
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        )
        connection.commit()
    
    return jsonify({"id": account_id}), 201