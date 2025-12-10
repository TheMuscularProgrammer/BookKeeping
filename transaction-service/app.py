from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from contextlib import contextmanager
import os
import jwt
import json
from kafka import KafkaProducer
import redis
from metrics_middleware import setup_metrics

app = Flask(__name__)
CORS(app)
setup_metrics(app)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:example@localhost:5432/mydatabase')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# Kafka Producer - ייצור הודעות ל-Kafka
kafka_producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Redis Client - לקאשינג מהיר
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Database setup
engine = create_engine(DATABASE_URL)

# סף אישור - העברות מעל $200 דורשות אישור ידני
APPROVAL_THRESHOLD = 20000  # 20000 cents = $200

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
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "transaction-service"}), 200

# ========== Endpoints הישנים (נשארים כמו שהם) ==========

@app.route('/transactions/<account_id>/deposit', methods=['POST'])
def deposit(account_id):
    """Deposit money to account"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    user_id = verify_user(token)
    
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    
    with get_db_connection() as connection:
        # Check account ownership
        account = connection.execute(
            text('SELECT * FROM accounts WHERE id = :account_id AND owner_id = :user_id'),
            {'account_id': account_id, 'user_id': user_id}
        ).fetchone()
        
        if not account:
            return jsonify({"error": "Account not found or unauthorized"}), 403
        
        # Update balance
        connection.execute(
            text('UPDATE accounts SET balance_cents = balance_cents + :amount, updated_at = :updated_at WHERE id = :account_id'),
            {'amount': amount, 'account_id': account_id, 'updated_at': datetime.now()}
        )
        
        # Create transaction record
        transaction_id = str(uuid.uuid4())
        connection.execute(
            text("""
                INSERT INTO transactions 
                (id, initiator_id, to_bank_account_id, amount, created_at, updated_at)
                VALUES (:id, :initiator_id, :to_bank_account_id, :amount, :created_at, :updated_at)
            """),
            {
                'id': transaction_id,
                'initiator_id': user_id,
                'to_bank_account_id': account_id,
                'amount': amount,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        )
    
    return jsonify({"message": "Deposit successful", "transaction_id": transaction_id}), 200

@app.route('/transactions/<account_id>/withdraw', methods=['POST'])
def withdraw(account_id):
    """Withdraw money from account"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    user_id = verify_user(token)
    
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    
    with get_db_connection() as connection:
        # Check account ownership and balance
        account = connection.execute(
            text('SELECT * FROM accounts WHERE id = :account_id AND owner_id = :user_id'),
            {'account_id': account_id, 'user_id': user_id}
        ).fetchone()
        
        if not account:
            return jsonify({"error": "Account not found or unauthorized"}), 403
        
        if account.balance_cents < amount:
            return jsonify({"error": "Insufficient funds", "current_balance": account.balance_cents}), 400
        
        # Update balance
        connection.execute(
            text('UPDATE accounts SET balance_cents = balance_cents - :amount, updated_at = :updated_at WHERE id = :account_id'),
            {'amount': amount, 'account_id': account_id, 'updated_at': datetime.now()}
        )
        
        # Create transaction record
        transaction_id = str(uuid.uuid4())
        connection.execute(
            text("""
                INSERT INTO transactions 
                (id, initiator_id, from_bank_account_id, amount, created_at, updated_at)
                VALUES (:id, :initiator_id, :from_bank_account_id, :amount, :created_at, :updated_at)
            """),
            {
                'id': transaction_id,
                'initiator_id': user_id,
                'from_bank_account_id': account_id,
                'amount': amount,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        )
    
    return jsonify({"message": "Withdrawal successful", "transaction_id": transaction_id}), 200

# ========== Endpoints חדשים! ==========

@app.route('/transactions/<from_account_id>/transfer', methods=['POST'])
def transfer(from_account_id):
    """Create a transfer request - יעובד אסינכרונית דרך Kafka"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    user_id = verify_user(token)
    
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    data = request.get_json()
    amount = data.get('amount')
    to_account_id = data.get('to_account_id')
    
    if not amount or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    
    if not to_account_id:
        return jsonify({"error": "Destination account required"}), 400
    
    with get_db_connection() as connection:
        # Check source account
        from_account = connection.execute(
            text('SELECT * FROM accounts WHERE id = :from_account_id AND owner_id = :user_id'),
            {'from_account_id': from_account_id, 'user_id': user_id}
        ).fetchone()
        
        if not from_account:
            return jsonify({"error": "Source account not found or unauthorized"}), 403
        
        if from_account.balance_cents < amount:
            return jsonify({"error": "Insufficient funds", "current_balance": from_account.balance_cents}), 400
        
        # Check destination account exists
        to_account = connection.execute(
            text('SELECT id FROM accounts WHERE id = :to_account_id'),
            {'to_account_id': to_account_id}
        ).fetchone()
        
        if not to_account:
            return jsonify({"error": "Destination account not found"}), 404
        
        # 🎯 החלטה: צריך אישור או לא?
        requires_approval = amount > APPROVAL_THRESHOLD
        initial_state = "pending" if requires_approval else "approved"
        
        # Create transfer request בטבלה
        transfer_request_id = str(uuid.uuid4())
        connection.execute(
            text("""
                INSERT INTO transfer_requests 
                (id, initiator_id, from_account_id, to_account_id, amount, state, requires_approval, created_at, updated_at)
                VALUES (:id, :initiator_id, :from_account_id, :to_account_id, :amount, :state, :requires_approval, :created_at, :updated_at)
            """),
            {
                'id': transfer_request_id,
                'initiator_id': user_id,
                'from_account_id': from_account_id,
                'to_account_id': to_account_id,
                'amount': amount,
                'state': initial_state,
                'requires_approval': requires_approval,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        )
        
        # 💾 שמירה ב-Redis לגישה מהירה
        redis_client.hset(
            f"transfer:{transfer_request_id}",
            mapping={
                'state': initial_state,
                'amount': amount,
                'from_account_id': from_account_id,
                'to_account_id': to_account_id,
                'requires_approval': str(requires_approval)
            }
        )
        redis_client.expire(f"transfer:{transfer_request_id}", 86400)  # TTL: 24 שעות
        
        # 📨 שליחה ל-Kafka לעיבוד
        kafka_message = {
            'transfer_request_id': transfer_request_id,
            'initiator_id': user_id,
            'from_account_id': from_account_id,
            'to_account_id': to_account_id,
            'amount': amount,
            'state': initial_state,
            'requires_approval': requires_approval,
            'timestamp': datetime.now().isoformat()
        }
        
        kafka_producer.send('transfer-requests', value=kafka_message)
        kafka_producer.flush()
    
    return jsonify({
        "message": "Transfer request created",
        "transfer_request_id": transfer_request_id,
        "state": initial_state,
        "requires_approval": requires_approval
    }), 202  # 202 Accepted - יעובד אסינכרונית

@app.route('/transfers/<transfer_request_id>/status', methods=['GET'])
def get_transfer_status(transfer_request_id):
    """Get transfer request status - מ-Redis (מהיר!) או מ-DB"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    user_id = verify_user(token)
    
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    # 🚀 נסיון ראשון: Redis (מהיר!)
    redis_data = redis_client.hgetall(f"transfer:{transfer_request_id}")
    
    if redis_data:
        return jsonify({
            "transfer_request_id": transfer_request_id,
            "state": redis_data.get('state'),
            "amount": int(redis_data.get('amount', 0)),
            "requires_approval": redis_data.get('requires_approval') == 'True',
            "source": "redis"
        }), 200
    
    # 🐢 Fallback: Database (יותר איטי)
    with get_db_connection() as connection:
        transfer = connection.execute(
            text('SELECT * FROM transfer_requests WHERE id = :id AND initiator_id = :initiator_id'),
            {'id': transfer_request_id, 'initiator_id': user_id}
        ).fetchone()
        
        if not transfer:
            return jsonify({"error": "Transfer request not found"}), 404
        
        return jsonify({
            "transfer_request_id": str(transfer.id),
            "state": transfer.state,
            "amount": transfer.amount,
            "requires_approval": transfer.requires_approval,
            "transaction_id": str(transfer.transaction_id) if transfer.transaction_id else None,
            "created_at": transfer.created_at.isoformat(),
            "updated_at": transfer.updated_at.isoformat(),
            "source": "database"
        }), 200

@app.route('/transfers/<transfer_request_id>/approve', methods=['POST'])
def approve_transfer(transfer_request_id):
    """Approve a pending transfer (אישור ידני)"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    user_id = verify_user(token)
    
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    with get_db_connection() as connection:
        # Get transfer request
        transfer = connection.execute(
            text('SELECT * FROM transfer_requests WHERE id = :id'),
            {'id': transfer_request_id}
        ).fetchone()
        
        if not transfer:
            return jsonify({"error": "Transfer request not found"}), 404
        
        if transfer.state != 'pending':
            return jsonify({"error": f"Transfer is in '{transfer.state}' state, cannot approve"}), 400
        
        # Update state to approved
        connection.execute(
            text("""
                UPDATE transfer_requests 
                SET state = 'approved', approved_by = :approved_by, updated_at = :updated_at 
                WHERE id = :id
            """),
            {
                'id': transfer_request_id,
                'approved_by': user_id,
                'updated_at': datetime.now()
            }
        )
        
        # Update Redis
        redis_client.hset(f"transfer:{transfer_request_id}", 'state', 'approved')
        
        # 📨 שליחה ל-Kafka שהעברה אושרה
        kafka_message = {
            'transfer_request_id': transfer_request_id,
            'state': 'approved',
            'approved_by': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        kafka_producer.send('transfer-approvals', value=kafka_message)
        kafka_producer.flush()
    
    return jsonify({
        "message": "Transfer approved",
        "transfer_request_id": transfer_request_id,
        "state": "approved"
    }), 200

@app.route('/transfers/<transfer_request_id>/decline', methods=['POST'])
def decline_transfer(transfer_request_id):
    """Decline a pending transfer (דחייה)"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    user_id = verify_user(token)
    
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    data = request.get_json()
    decline_reason = data.get('reason', 'Declined by administrator')
    
    with get_db_connection() as connection:
        # Get transfer request
        transfer = connection.execute(
            text('SELECT * FROM transfer_requests WHERE id = :id'),
            {'id': transfer_request_id}
        ).fetchone()
        
        if not transfer:
            return jsonify({"error": "Transfer request not found"}), 404
        
        if transfer.state != 'pending':
            return jsonify({"error": f"Transfer is in '{transfer.state}' state, cannot decline"}), 400
        
        # Update state to declined
        connection.execute(
            text("""
                UPDATE transfer_requests 
                SET state = 'declined', decline_reason = :reason, updated_at = :updated_at 
                WHERE id = :id
            """),
            {
                'id': transfer_request_id,
                'reason': decline_reason,
                'updated_at': datetime.now()
            }
        )
        
        # Update Redis
        redis_client.hset(f"transfer:{transfer_request_id}", 'state', 'declined')
        
        # 📨 שליחה ל-Kafka שהעברה נדחתה
        kafka_message = {
            'transfer_request_id': transfer_request_id,
            'state': 'declined',
            'decline_reason': decline_reason,
            'timestamp': datetime.now().isoformat()
        }
        
        kafka_producer.send('transfer-declines', value=kafka_message)
        kafka_producer.flush()
    
    return jsonify({
        "message": "Transfer declined",
        "transfer_request_id": transfer_request_id,
        "state": "declined",
        "reason": decline_reason
    }), 200

@app.route('/transactions/<account_id>/history', methods=['GET'])
def get_transaction_history(account_id):
    """Get transaction history for account"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    user_id = verify_user(token)
    
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    with get_db_connection() as connection:
        # Check account ownership
        account = connection.execute(
            text('SELECT * FROM accounts WHERE id = :account_id AND owner_id = :user_id'),
            {'account_id': account_id, 'user_id': user_id}
        ).fetchone()
        
        if not account:
            return jsonify({"error": "Account not found or unauthorized"}), 403
        
        # Get transactions
        transactions = connection.execute(
            text("""
                SELECT * FROM transactions 
                WHERE from_bank_account_id = :account_id 
                OR to_bank_account_id = :account_id 
                ORDER BY created_at DESC
            """),
            {'account_id': account_id}
        ).fetchall()
        
        transaction_list = [
            {
                'id': str(t.id),
                'type': 'withdrawal' if str(t.from_bank_account_id) == account_id else 'deposit',
                'amount': t.amount,
                'from_account': str(t.from_bank_account_id) if t.from_bank_account_id else None,
                'to_account': str(t.to_bank_account_id) if t.to_bank_account_id else None,
                'created_at': t.created_at.isoformat()
            }
            for t in transactions
        ]
    
    return jsonify({"transactions": transaction_list}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)