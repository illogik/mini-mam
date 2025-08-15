from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.utils import setup_logging
from shared.metrics import setup_metrics_endpoint, record_request_metrics, metrics_middleware, cleanup_metrics
from shared.auth import authenticate_user, generate_token, require_auth, require_role, optional_auth
setup_logging("api-gateway")

app = Flask(__name__)
CORS(app)

# Configure maximum content length for file uploads (100MB)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Setup metrics
metrics_port = int(os.getenv('API_GATEWAY_METRICS_PORT', 9090))
setup_metrics_endpoint(app, metrics_port)

# Service URLs
SERVICES = {
    'assets': os.getenv('ASSETS_SERVICE_URL', 'http://localhost:8001'),
    'files': os.getenv('FILES_SERVICE_URL', 'http://localhost:8002'),
    'transcode': os.getenv('TRANSCODE_SERVICE_URL', 'http://localhost:8003'),
    'search': os.getenv('SEARCH_SERVICE_URL', 'http://localhost:8004')
}

# Add request metrics middleware
@app.before_request
def before_request():
    request.start_time = metrics_middleware()(request)

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        record_request_metrics(request.start_time, request, response)
    return response

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": "2024-01-01T00:00:00Z"
    })

# Authentication endpoints
@app.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Login endpoint to obtain JWT token"""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'error': 'Missing credentials',
                'message': 'Username and password are required'
            }), 400
        
        username = data['username']
        password = data['password']
        
        # Authenticate user
        user = authenticate_user(username, password)
        if not user:
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Invalid username or password'
            }), 401
        
        # Generate JWT token
        token = generate_token(user['user_id'], user['username'], user['role'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role']
            }
        }), 200
    
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred during login'
        }), 500

@app.route('/auth/verify', methods=['POST'])
@limiter.limit("100 per minute")
@require_auth
def verify_token():
    """Verify JWT token endpoint"""
    return jsonify({
        'message': 'Token is valid',
        'user': request.user
    }), 200

@app.route('/auth/me', methods=['GET'])
@limiter.limit("100 per minute")
@require_auth
def get_current_user():
    """Get current user information"""
    return jsonify({
        'user': request.user
    }), 200

# Protected API endpoints
@app.route('/api/assets', methods=['GET', 'POST'])
@app.route('/api/assets/', methods=['GET', 'POST'])
@app.route('/api/assets/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@limiter.limit("100 per minute")
@require_auth
def assets_proxy(subpath=None):
    """Proxy requests to assets service"""
    return proxy_request('assets', request, subpath)

@app.route('/api/files', methods=['GET', 'POST'])
@app.route('/api/files/', methods=['GET', 'POST'])
@app.route('/api/files/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@limiter.limit("50 per minute")
@require_auth
def files_proxy(subpath=None):
    """Proxy requests to files service"""
    return proxy_request('files', request, subpath)

@app.route('/api/transcode', methods=['GET', 'POST'])
@app.route('/api/transcode/', methods=['GET', 'POST'])
@app.route('/api/transcode/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@limiter.limit("30 per minute")
@require_auth
def transcode_proxy(subpath=None):
    """Proxy requests to transcode service"""
    return proxy_request('transcode', request, subpath)

@app.route('/api/search', methods=['GET', 'POST'])
@app.route('/api/search/', methods=['GET', 'POST'])
@app.route('/api/search/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@limiter.limit("200 per minute")
@require_auth  # Search now requires authentication
def search_proxy(subpath=None):
    """Proxy requests to search service"""
    return proxy_request('search', request, subpath)

def proxy_request(service_name, request, subpath=None):
    """Proxy request to appropriate microservice"""
    try:
        service_url = SERVICES[service_name]
        
        # Build target URL with /api prefix
        if subpath:
            target_url = f"{service_url}/api/{service_name}/{subpath}"
        else:
            target_url = f"{service_url}/api/{service_name}"
        
        # Prepare headers
        headers = {
            'Content-Type': request.headers.get('Content-Type', 'application/json'),
            'Authorization': request.headers.get('Authorization', ''),
            'User-Agent': 'API-Gateway'
        }
        
        # Add user information to headers if available
        if hasattr(request, 'user') and request.user:
            headers['X-User-ID'] = str(request.user.get('user_id', ''))
            headers['X-Username'] = request.user.get('username', '')
            headers['X-User-Role'] = request.user.get('role', '')
        
        # Remove headers that shouldn't be forwarded
        for header in ['Host', 'Content-Length']:
            headers.pop(header, None)
        
        logging.info(f"Proxying request to {target_url} with headers {headers}")

        # Make request to microservice
        if request.method == 'GET':
            response = requests.get(target_url, headers=headers, params=request.args)
        elif request.method == 'POST':
            response = requests.post(target_url, headers=headers, json=request.get_json())
        elif request.method == 'PUT':
            response = requests.put(target_url, headers=headers, json=request.get_json())
        elif request.method == 'DELETE':
            response = requests.delete(target_url, headers=headers)
        else:
            return jsonify({"error": "Method not allowed"}), 405
        
        # Return response from microservice
        return response.content, response.status_code, response.headers.items()
    
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"{service_name} service unavailable"}), 503
    except Exception as e:
        logging.error(f"Error proxying request to {service_name}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/status', methods=['GET'])
@limiter.limit("50 per minute")
@require_auth
def service_status():
    """Check status of all microservices"""
    status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            status[service_name] = {
                "status": "unavailable",
                "error": str(e)
            }
    
    return jsonify({
        "gateway": "healthy",
        "services": status
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Setup cleanup for multiprocess metrics
    cleanup_metrics()
    
    port = int(os.getenv('API_GATEWAY_PORT', 8000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    ) 