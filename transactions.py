from flask import Blueprint, request, jsonify
from db import get_db_connection  

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    amount = data.get('amount')
    account_id = data.get('account_id')
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('UPDATE accounts SET balance_cents = balance_cents + %s WHERE id = %s', (amount, account_id))
    connection.commit()
    return jsonify({"message": "Deposit successful"}), 200

@transactions_bp.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json()
    amount = data.get('amount')
    account_id = data.get('account_id')
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('UPDATE accounts SET balance_cents = balance_cents - %s WHERE id = %s', (amount, account_id))
    connection.commit()
    return jsonify({"message": "Withdrawal successful"}), 200

@transactions_bp.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    amount = data.get('amount')
    from_account_id = data.get('from_account_id')
    to_account_id = data.get('to_account_id')

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('UPDATE accounts SET balance_cents = balance_cents - %s WHERE id = %s', (amount, from_account_id))
    cursor.execute('UPDATE accounts SET balance_cents = balance_cents + %s WHERE id = %s', (amount, to_account_id))
    connection.commit()
    return jsonify({"message": "Transfer successful"}), 200
