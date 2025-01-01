from flask import Blueprint, request, jsonify
from db import get_db_connection
from sqlalchemy import text
from middleware import jwt_required_with_user_id
from datetime import datetime
import uuid

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/<account_id>/deposit', methods=['POST'])
@jwt_required_with_user_id
def deposit(current_user_id, account_id):
    data = request.get_json()
    amount = data.get('amount')
    
    with get_db_connection() as connection:
        # Check account ownership
        account = connection.execute(
            text('SELECT * FROM accounts WHERE id = :account_id AND owner_id = :user_id'),
            {'account_id': account_id, 'user_id': current_user_id}
        ).fetchone()
        
        if not account:
            return jsonify({"error": "Account not found or unauthorized"}), 403
        
        # Update balance
        connection.execute(
            text('UPDATE accounts SET balance_cents = balance_cents + :amount WHERE id = :account_id'),
            {'amount': amount, 'account_id': account_id}
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
                'initiator_id': current_user_id,
                'to_bank_account_id': account_id,
                'amount': amount,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        )
    
    return jsonify({"message": "Deposit successful", "transaction_id": transaction_id}), 200

@transactions_bp.route('/<account_id>/withdraw', methods=['POST'])
@jwt_required_with_user_id
def withdraw(current_user_id, account_id):
    data = request.get_json()
    amount = data.get('amount')
    
    with get_db_connection() as connection:
        # Check account ownership
        account = connection.execute(
            text('SELECT * FROM accounts WHERE id = :account_id AND owner_id = :user_id'),
            {'account_id': account_id, 'user_id': current_user_id}
        ).fetchone()
        
        if not account:
            return jsonify({"error": "Account not found or unauthorized"}), 403
        
        # Check balance
        current_balance = connection.execute(
            text('SELECT balance_cents FROM accounts WHERE id = :account_id'),
            {'account_id': account_id}
        ).scalar()

        if current_balance < amount:
            return jsonify({"error": "Insufficient funds", "current_balance": current_balance}), 400
        
        # Update balance
        connection.execute(
            text('UPDATE accounts SET balance_cents = balance_cents - :amount WHERE id = :account_id'),
            {'amount': amount, 'account_id': account_id}
        )
        
        # Create transaction record
        transaction_id = str(uuid.uuid4())
        connection.execute(
            text("""
                INSERT INTO transactions 
                (id, initiator_id, from_bank_account_id, amount, created_at, updated_at)
                VALUES (:id, :initiator_id, :account_id, :amount, :created_at, :updated_at)
            """),
            {
                'id': transaction_id,
                'initiator_id': current_user_id,
                'account_id': account_id,
                'amount': amount,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        )
    
    return jsonify({"message": "Withdrawal successful", "transaction_id": transaction_id}), 200

@transactions_bp.route('/<from_account_id>/transfer', methods=['POST'])
@jwt_required_with_user_id
def transfer(current_user_id, from_account_id):
    data = request.get_json()
    amount = data.get('amount')
    to_account_id = data.get('to_account_id')
    
    with get_db_connection() as connection:
        # Check source account ownership
        from_account = connection.execute(
            text('SELECT * FROM accounts WHERE id = :from_account_id AND owner_id = :user_id'),
            {'from_account_id': from_account_id, 'user_id': current_user_id}
        ).fetchone()
        
        if not from_account:
            return jsonify({"error": "Source account not found or unauthorized"}), 403
        
        # Check sufficient balance
        if from_account.balance_cents < amount:
            return jsonify({"error": "Insufficient funds", 
                          "current_balance": from_account.balance_cents}), 400
        
        # Check destination account exists
        to_account = connection.execute(
            text('SELECT id FROM accounts WHERE id = :to_account_id'),
            {'to_account_id': to_account_id}
        ).fetchone()
        
        if not to_account:
            return jsonify({"error": "Destination account not found"}), 404
        
        # Update balances
        connection.execute(
            text('UPDATE accounts SET balance_cents = balance_cents - :amount WHERE id = :from_account_id'),
            {'amount': amount, 'from_account_id': from_account_id}
        )
        connection.execute(
            text('UPDATE accounts SET balance_cents = balance_cents + :amount WHERE id = :to_account_id'),
            {'amount': amount, 'to_account_id': to_account_id}
        )
        
        # Create transaction record
        transaction_id = str(uuid.uuid4())
        connection.execute(
            text("""
                INSERT INTO transactions 
                (id, initiator_id, from_bank_account_id, to_bank_account_id, amount, created_at, updated_at)
                VALUES (:id, :initiator_id, :from_account_id, :to_account_id, :amount, :created_at, :updated_at)
            """),
            {
                'id': transaction_id,
                'initiator_id': current_user_id,
                'from_account_id': from_account_id,
                'to_account_id': to_account_id,
                'amount': amount,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        )
    
    return jsonify({"message": "Transfer successful", "transaction_id": transaction_id}), 200

@transactions_bp.route('/<account_id>/transactions', methods=['GET'])
@jwt_required_with_user_id
def get_account_transactions(current_user_id, account_id):
    with get_db_connection() as connection:
        # Check account ownership
        account = connection.execute(
            text('SELECT * FROM accounts WHERE id = :account_id AND owner_id = :user_id'),
            {'account_id': account_id, 'user_id': current_user_id}
        ).fetchone()
        
        if not account:
            return jsonify({"error": "Account not found or unauthorized"}), 403
        
        # Get all transactions for this account
        transactions = connection.execute(
            text("""
                SELECT * FROM transactions 
                WHERE from_bank_account_id = :account_id 
                OR to_bank_account_id = :account_id 
                ORDER BY created_at DESC
            """),
            {'account_id': account_id}
        ).fetchall()
        
        # Convert to list of dictionaries
        transactions_list = []
        for t in transactions:
            transactions_list.append({
                'id': t.id,
                'type': 'withdrawal' if t.from_bank_account_id == account_id else 'deposit',
                'amount': t.amount,
                'from_account': t.from_bank_account_id,
                'to_account': t.to_bank_account_id,
                'created_at': t.created_at.isoformat(),
            })
    
    return jsonify({"transactions": transactions_list}), 200