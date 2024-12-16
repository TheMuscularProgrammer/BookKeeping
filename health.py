from flask import Blueprint, jsonify
from sqlalchemy import text  # הוסף שורה זו
from db import get_db_connection

health_bp = Blueprint('health_bp', __name__)

@health_bp.route('/status', methods=['GET'])
def status():
    try:
        with get_db_connection() as connection:
            connection.execute(text("SELECT 1")).fetchone()  # שים לב לשינוי כאן
            return jsonify({"status": "ok", "message": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500

@health_bp.route('/version', methods=['GET'])
def version():
    return jsonify({"version": "0.0.1"}), 200