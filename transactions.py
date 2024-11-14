from flask import Blueprint, request, jsonify
from db import get_db_connection
from sqlalchemy import text

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    amount = data.get('amount')
    account_id = data.get('account_id')
    
    with get_db_connection() as connection:
        connection.execute(
            text('UPDATE accounts SET balance_cents = balance_cents + :amount WHERE id = :account_id'),
            {'amount': amount, 'account_id': account_id}
        )
        connection.commit()
    
    return jsonify({"message": "Deposit successful"}), 200

@transactions_bp.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json()
    amount = data.get('amount')
    account_id = data.get('account_id')
    
    with get_db_connection() as connection:
        connection.execute(
            text('UPDATE accounts SET balance_cents = balance_cents - :amount WHERE id = :account_id'),
            {'amount': amount, 'account_id': account_id}
        )
        connection.commit()
    
    return jsonify({"message": "Withdrawal successful"}), 200

@transactions_bp.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    amount = data.get('amount')
    from_account_id = data.get('from_account_id')
    to_account_id = data.get('to_account_id')

    with get_db_connection() as connection:
        connection.execute(
            text('UPDATE accounts SET balance_cents = balance_cents - :amount WHERE id = :from_account_id'),
            {'amount': amount, 'from_account_id': from_account_id}
        )
        connection.execute(
            text('UPDATE accounts SET balance_cents = balance_cents + :amount WHERE id = :to_account_id'),
            {'amount': amount, 'to_account_id': to_account_id}
        )
        connection.commit()
    
    return jsonify({"message": "Transfer successful"}), 200
