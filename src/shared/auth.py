from flask import request, jsonify
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

def get_hardcoded_users():
    """Get hardcoded user credentials from environment variables"""
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    user_password = os.getenv('USER_PASSWORD', 'user123')
    
    return {
        'admin': {
            'password_hash': generate_password_hash(admin_password),
            'role': 'admin',
            'user_id': 1
        },
        'user': {
            'password_hash': generate_password_hash(user_password),
            'role': 'user',
            'user_id': 2
        }
    }

# Get user credentials from environment variables
HARDCODED_USERS = get_hardcoded_users()

def get_jwt_secret():
    """Get JWT secret from environment or use default"""
    return os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')

def generate_token(user_id, username, role):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm='HS256')

def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def authenticate_user(username, password):
    """Authenticate user with username and password"""
    if username not in HARDCODED_USERS:
        return None
    
    user = HARDCODED_USERS[username]
    if check_password_hash(user['password_hash'], password):
        return {
            'user_id': user['user_id'],
            'username': username,
            'role': user['role']
        }
    return None

def get_token_from_header():
    """Extract token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    # Check for Bearer token
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    
    return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                'error': 'Authentication required',
                'message': 'No token provided'
            }), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Invalid or expired token'
            }), 401
        
        # Add user info to request context
        request.user = payload
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(required_role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = get_token_from_header()
            
            if not token:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'No token provided'
                }), 401
            
            payload = verify_token(token)
            if not payload:
                return jsonify({
                    'error': 'Authentication failed',
                    'message': 'Invalid or expired token'
                }), 401
            
            # Check role
            if payload.get('role') != required_role:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'Role {required_role} required'
                }), 403
            
            # Add user info to request context
            request.user = payload
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def optional_auth(f):
    """Decorator for optional authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        
        if token:
            payload = verify_token(token)
            if payload:
                request.user = payload
            else:
                request.user = None
        else:
            request.user = None
        
        return f(*args, **kwargs)
    
    return decorated_function 