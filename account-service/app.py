from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from contextlib import contextmanager
import os


app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:example@localhost:5432/mydatabase')


# Database setup
engine = create_engine(DATABASE_URL)

@contextmanager
def get_db_connection():
    connection = engine.connect()
    transaction = connection.begin()
    try:
        yield connection
        transaction.commit()
    except Exception as e:
        transaction.rollback()
        raise
    finally:
        connection.close()

def verify_user(token):
    """Verify user token with User Service (gRPC call in future)"""
    # TODO: Call User Service via gRPC to verify token
    # For now, we'll do simple JWT decode
    import jwt
    try:
        payload = jwt.decode(token, os.environ.get('JWT_SECRET_KEY', 'dev-secret-key'), algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "account-service"}), 200

@app.route('/accounts', methods=['POST'])
def create_account():
    """Create a new bank account"""
    # Get token from header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    user_id = verify_user(token)
    
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    data = request.get_json()
    
    account_id = str(uuid.uuid4())
    account_number = str(uuid.uuid4())
    
    with get_db_connection() as connection:
        connection.execute(
            text(
                "INSERT INTO accounts (id, owner_id, account_number, type, balance_cents, created_at, updated_at) "
                "VALUES (:account_id, :owner_id, :account_number, :type, :balance_cents, :created_at, :updated_at)"
            ),
            {
                'account_id': account_id,
                'owner_id': user_id,
                'account_number': account_number,
                'type': data.get('type', 'checking'),
                'balance_cents': data.get('balance_cents', 0),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        )
    
    return jsonify({"id": account_id, "account_number": account_number}), 201

@app.route('/accounts', methods=['GET'])
def list_accounts():
    """List all accounts for authenticated user"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    user_id = verify_user(token)
    
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    with get_db_connection() as connection:
        accounts = connection.execute(
            text("SELECT * FROM accounts WHERE owner_id = :owner_id"),
            {'owner_id': user_id}
        ).fetchall()
        
        account_list = [
            {
                'id': str(acc.id),
                'account_number': acc.account_number,
                'type': acc.type,
                'balance_cents': acc.balance_cents,
                'created_at': acc.created_at.isoformat()
            }
            for acc in accounts
        ]
    
    return jsonify({"accounts": account_list}), 200

@app.route('/accounts/<account_id>', methods=['GET'])
def get_account(account_id):
    """Get specific account details"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    user_id = verify_user(token)
    
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    with get_db_connection() as connection:
        account = connection.execute(
            text("SELECT * FROM accounts WHERE id = :account_id AND owner_id = :owner_id"),
            {'account_id': account_id, 'owner_id': user_id}
        ).fetchone()
        
        if not account:
            return jsonify({"error": "Account not found"}), 404
        
        return jsonify({
            'id': str(account.id),
            'account_number': account.account_number,
            'type': account.type,
            'balance_cents': account.balance_cents,
            'created_at': account.created_at.isoformat()
        }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)