from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify

def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role != role and user_role != "admin":
                return jsonify({"msg": "Insufficient privileges"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def roles_allowed(roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in roles:
                return jsonify({"msg": "Insufficient privileges"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
