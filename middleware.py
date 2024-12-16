from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def jwt_required_with_user_id(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            kwargs['current_user_id'] = current_user_id
            return fn(*args, **kwargs)
        
        except Exception as e:
            return jsonify({"msg": "Missing or invalid token"}), 401
    
    return wrapper