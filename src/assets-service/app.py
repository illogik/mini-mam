from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.utils import setup_logging, create_response
from shared.metrics import (
    setup_metrics_endpoint, record_request_metrics, metrics_middleware,
    db_operation_timer, cleanup_metrics
)
from prometheus_client import Counter
setup_logging("assets-service")

app = Flask(__name__)
CORS(app)

# Assets Service specific metrics
ASSETS_CREATED = Counter(
    'assets_created_total',
    'Total number of assets created'
)

ASSETS_UPDATED = Counter(
    'assets_updated_total',
    'Total number of assets updated'
)

ASSETS_DELETED = Counter(
    'assets_deleted_total',
    'Total number of assets deleted'
)

ASSETS_RETRIEVED = Counter(
    'assets_retrieved_total',
    'Total number of assets retrieved'
)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///assets.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

db = SQLAlchemy(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)

# Setup metrics
metrics_port = int(os.getenv('ASSETS_SERVICE_METRICS_PORT', 9091))
setup_metrics_endpoint(app, metrics_port)

# Add request metrics middleware
@app.before_request
def before_request():
    request.start_time = metrics_middleware()(request)

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        record_request_metrics(request.start_time, request, response)
    return response

# Create Flask-SQLAlchemy compatible Asset model
class Asset(db.Model):
    """Asset model for managing digital assets"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    file_id = db.Column(db.Integer)  # Reference to uploaded file
    asset_metadata = db.Column(db.JSON)
    tags = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

# Initialize database tables
with app.app_context():
    db.create_all()

def get_presigned_url_from_files_service(file_id):
    """Get a pre-signed URL for downloading a file from the files service"""
    try:
        files_service_url = os.getenv('FILES_SERVICE_URL', 'http://localhost:8002')
        response = requests.get(f"{files_service_url}/api/files/{file_id}/presigned-url", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                return data['data'].get('presigned_url')
            return data.get('presigned_url')
        else:
            logging.error(f"Failed to get pre-signed URL for file {file_id}: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error getting pre-signed URL for file {file_id}: {e}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "assets-service",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/assets', methods=['GET'])
@limiter.limit("100 per minute")
def get_assets():
    """Get all assets with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        tags = request.args.get('tags', '')
        
        query = Asset.query.filter(Asset.is_active == True)
        
        if search:
            query = query.filter(Asset.name.contains(search) | Asset.description.contains(search))
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            # Simple tag filtering - in production you'd want more sophisticated search
            for tag in tag_list:
                query = query.filter(Asset.tags.contains([tag]))
        
        assets = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify(create_response(
            data={
                "assets": [asset_to_dict(asset) for asset in assets.items],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": assets.total,
                    "pages": assets.pages
                }
            }
        ))
    
    except Exception as e:
        logging.error(f"Error getting assets: {e}")
        return jsonify(create_response(error="Failed to retrieve assets", status_code=500)), 500

@app.route('/api/assets', methods=['POST'])
@limiter.limit("50 per minute")
def create_asset():
    """Create a new asset"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify(create_response(error="Name is required", status_code=400)), 400
        
        # Check if asset with same name already exists
        with db_operation_timer('select', 'assets'):
            existing_asset = Asset.query.filter_by(name=data['name'], is_active=True).first()
        if existing_asset:
            return jsonify(create_response(error="Asset with this name already exists", status_code=409)), 409
        
        asset = Asset(
            name=data['name'],
            description=data.get('description', ''),
            file_path=data.get('file_path', ''),
            file_size=data.get('file_size'),
            mime_type=data.get('mime_type'),
            file_id=data.get('file_id'),
            asset_metadata=data.get('metadata', {}),  # Use asset_metadata field name
            tags=data.get('tags', [])
        )
        
        with db_operation_timer('insert', 'assets'):
            db.session.add(asset)
            db.session.commit()
        
        # Record business metric
        ASSETS_CREATED.inc()
        
        return jsonify(create_response(
            data=asset_to_dict(asset),
            message="Asset created successfully"
        )), 201
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating asset: {e}")
        return jsonify(create_response(error="Failed to create asset", status_code=500)), 500

@app.route('/api/assets/<int:asset_id>', methods=['GET'])
@limiter.limit("200 per minute")
def get_asset(asset_id):
    """Get a specific asset by ID"""
    try:
        asset = Asset.query.filter_by(id=asset_id, is_active=True).first()
        
        if not asset:
            return jsonify(create_response(error="Asset not found", status_code=404)), 404
        
        # Record business metric
        ASSETS_RETRIEVED.inc()
        
        return jsonify(create_response(data=asset_to_dict(asset)))
    
    except Exception as e:
        logging.error(f"Error getting asset {asset_id}: {e}")
        return jsonify(create_response(error="Failed to retrieve asset", status_code=500)), 500

@app.route('/api/assets/<int:asset_id>', methods=['PUT'])
@limiter.limit("50 per minute")
def update_asset(asset_id):
    """Update an asset"""
    try:
        asset = Asset.query.filter_by(id=asset_id, is_active=True).first()
        
        if not asset:
            return jsonify(create_response(error="Asset not found", status_code=404)), 404
        
        data = request.get_json()
        
        if 'name' in data:
            asset.name = data['name']
        if 'description' in data:
            asset.description = data['description']
        if 'file_path' in data:
            asset.file_path = data['file_path']
        if 'file_size' in data:
            asset.file_size = data['file_size']
        if 'mime_type' in data:
            asset.mime_type = data['mime_type']
        if 'file_id' in data:
            asset.file_id = data['file_id']
        if 'metadata' in data:
            asset.asset_metadata = data['metadata']  # Use asset_metadata field name
        if 'tags' in data:
            asset.tags = data['tags']
        
        asset.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Record business metric
        ASSETS_UPDATED.inc()
        
        return jsonify(create_response(
            data=asset_to_dict(asset),
            message="Asset updated successfully"
        ))
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating asset {asset_id}: {e}")
        return jsonify(create_response(error="Failed to update asset", status_code=500)), 500

@app.route('/api/assets/<int:asset_id>', methods=['DELETE'])
@limiter.limit("20 per minute")
def delete_asset(asset_id):
    """Soft delete an asset"""
    try:
        asset = Asset.query.filter_by(id=asset_id, is_active=True).first()
        
        if not asset:
            return jsonify(create_response(error="Asset not found", status_code=404)), 404
        
        asset.is_active = False
        asset.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Record business metric
        ASSETS_DELETED.inc()
        
        return jsonify(create_response(message="Asset deleted successfully"))
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting asset {asset_id}: {e}")
        return jsonify(create_response(error="Failed to delete asset", status_code=500)), 500

@app.route('/api/assets/<int:asset_id>/tags', methods=['POST'])
@limiter.limit("100 per minute")
def add_tags(asset_id):
    """Add tags to an asset"""
    try:
        asset = Asset.query.filter_by(id=asset_id, is_active=True).first()
        
        if not asset:
            return jsonify(create_response(error="Asset not found", status_code=404)), 404
        
        data = request.get_json()
        new_tags = data.get('tags', [])
        
        if not isinstance(new_tags, list):
            return jsonify(create_response(error="Tags must be a list", status_code=400)), 400
        
        current_tags = asset.tags or []
        updated_tags = list(set(current_tags + new_tags))  # Remove duplicates
        
        asset.tags = updated_tags
        asset.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(create_response(
            data={"tags": updated_tags},
            message="Tags added successfully"
        ))
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding tags to asset {asset_id}: {e}")
        return jsonify(create_response(error="Failed to add tags", status_code=500)), 500

def asset_to_dict(asset):
    """Convert asset object to dictionary"""
    import json
    
    # Safely serialize JSON fields
    def safe_json_serialize(data):
        if data is None:
            return None
        try:
            # If it's already a dict/list, return as is
            if isinstance(data, (dict, list)):
                return data
            # If it's a string, try to parse it
            if isinstance(data, str):
                return json.loads(data)
            # Otherwise, convert to string and try to parse
            return json.loads(str(data))
        except (json.JSONDecodeError, TypeError):
            # If all else fails, return as string
            return str(data) if data is not None else None
    
    # Get pre-signed URL if file_id is present
    url = asset.file_path  # Default to file_path
    if asset.file_id:
        presigned_url = get_presigned_url_from_files_service(asset.file_id)
        if presigned_url:
            url = presigned_url
    
    return {
        "id": asset.id,
        "name": asset.name,
        "description": asset.description,
        "file_path": asset.file_path,
        "url": url,  # Add URL field with pre-signed URL or file_path
        "file_size": asset.file_size,
        "mime_type": asset.mime_type,
        "file_id": asset.file_id,
        "metadata": safe_json_serialize(asset.asset_metadata),  # Use asset_metadata field name
        "tags": safe_json_serialize(asset.tags),
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
    }

@app.errorhandler(404)
def not_found(error):
    return jsonify(create_response(error="Endpoint not found", status_code=404)), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify(create_response(error="Internal server error", status_code=500)), 500

if __name__ == '__main__':
    # Setup cleanup for multiprocess metrics
    cleanup_metrics()
    
    with app.app_context():
        db.create_all()
    
    port = int(os.getenv('ASSETS_SERVICE_PORT', 8001))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    ) 