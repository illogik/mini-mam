import os
import hashlib
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from flask import current_app


def generate_uuid() -> str:
    """Generate a unique UUID string"""
    return str(uuid.uuid4())


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    return os.path.getsize(file_path)


def get_mime_type(file_path: str) -> str:
    """Get MIME type of a file"""
    import magic
    return magic.from_file(file_path, mime=True)


def ensure_directory_exists(directory: str) -> None:
    """Ensure a directory exists, create if it doesn't"""
    os.makedirs(directory, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    return filename


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def make_service_request(service_url: str, endpoint: str, method: str = 'GET', 
                        data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
    """Make HTTP request to another microservice"""
    url = f"{service_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    default_headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Flask-Microservice-Framework'
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=default_headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=default_headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=default_headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=default_headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Service request failed: {e}")
        raise


def construct_database_url(database_name: str) -> str:
    """Construct database URL with variable substitution from environment variables"""
    # Get database connection parameters from environment
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD', 'password')
    db_host = os.getenv('POSTGRES_HOST', 'postgres')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    
    # Construct the database URL
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{database_name}"


def create_response(data: Any = None, message: str = "Success", 
                   status_code: int = 200, error: str = None) -> Dict:
    """Create standardized API response"""
    response = {
        "message": message,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if error:
        response["error"] = error
    
    return response


def validate_json_schema(data: Dict, schema: Dict) -> bool:
    """Validate JSON data against a schema"""
    try:
        from jsonschema import validate
        validate(instance=data, schema=schema)
        return True
    except Exception as e:
        logging.error(f"JSON validation failed: {e}")
        return False


def setup_logging(service_name: str, log_level: str = "INFO") -> None:
    """Setup structured logging for a service"""
    import structlog
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper())
    )


def get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value from environment or app config"""
    # First try environment variable
    value = os.getenv(key)
    if value is not None:
        return value
    
    # Then try Flask app config
    if current_app:
        return current_app.config.get(key, default)
    
    return default


def is_valid_uuid(uuid_string: str) -> bool:
    """Check if a string is a valid UUID"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False 