from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import logging

logger = logging.getLogger(__name__)

def jwt_required_with_user_id(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # לוג של כל ההדרים
            logger.debug("All headers:")
            for header, value in request.headers.items():
                logger.debug(f"{header}: {value}")

            auth_header = request.headers.get('Authorization')
            logger.debug(f"Raw Authorization header: {auth_header}")
            
            if not auth_header:
                logger.error("No Authorization header found")
                return jsonify({"msg": "Missing Authorization header"}), 401
                
            parts = auth_header.split()
            if len(parts) != 2 or parts[0] != 'Bearer':
                logger.error(f"Invalid Authorization header format: {auth_header}")
                return jsonify({"msg": "Invalid Authorization header format"}), 401
                
            token = parts[1]
            logger.debug(f"Extracted token: {token[:20]}...")  # רק חלק מהטוקן ללוגים
            
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            logger.debug(f"Successfully verified user ID: {current_user_id}")
            
            kwargs['current_user_id'] = current_user_id
            return fn(*args, **kwargs)
        
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            logger.exception("Full traceback:")
            return jsonify({"msg": "Authentication error", "error": str(e)}), 401
    
    return wrapper