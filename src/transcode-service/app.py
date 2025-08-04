from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
import subprocess
import threading
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.utils import setup_logging, create_response, ensure_directory_exists
setup_logging("transcode-service")

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///transcode.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Transcode configuration
app.config['OUTPUT_FOLDER'] = os.getenv('OUTPUT_FOLDER', './transcoded')
app.config['TEMP_FOLDER'] = os.getenv('TEMP_FOLDER', './temp')

db = SQLAlchemy(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per hour"]
)

# Create Flask-SQLAlchemy compatible Transcode model
class Transcode(db.Model):
    """Transcode model for managing media conversions"""
    __tablename__ = 'transcodes'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer)  # Reference to asset, but no foreign key constraint
    source_format = db.Column(db.String(20), nullable=False)
    target_format = db.Column(db.String(20), nullable=False)
    output_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    progress = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Initialize database tables
with app.app_context():
    db.create_all()

# Ensure directories exist
ensure_directory_exists(app.config['OUTPUT_FOLDER'])
ensure_directory_exists(app.config['TEMP_FOLDER'])

# Supported formats
SUPPORTED_FORMATS = {
    'video': ['mp4', 'avi', 'mov', 'mkv', 'webm'],
    'audio': ['mp3', 'wav', 'aac', 'ogg', 'flac'],
    'image': ['jpg', 'png', 'gif', 'webp']
}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "transcode-service",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/transcode', methods=['GET'])
@limiter.limit("100 per minute")
def get_transcodes():
    """Get all transcodes with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        asset_id = request.args.get('asset_id', type=int)
        status = request.args.get('status', '')
        
        query = Transcode.query
        
        if asset_id:
            query = query.filter(Transcode.asset_id == asset_id)
        
        if status:
            query = query.filter(Transcode.status == status)
        
        transcodes = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify(create_response(
            data={
                "transcodes": [transcode_to_dict(transcode) for transcode in transcodes.items],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": transcodes.total,
                    "pages": transcodes.pages
                }
            }
        ))
    
    except Exception as e:
        logging.error(f"Error getting transcodes: {e}")
        return jsonify(create_response(error="Failed to retrieve transcodes", status_code=500)), 500

@app.route('/api/transcode', methods=['POST'])
@limiter.limit("10 per minute")
def create_transcode():
    """Create a new transcode job"""
    try:
        data = request.get_json()
        
        if not data or 'asset_id' not in data or 'target_format' not in data:
            return jsonify(create_response(error="Asset ID and target format are required", status_code=400)), 400
        
        asset_id = data['asset_id']
        target_format = data['target_format']
        source_format = data.get('source_format', '')
        
        # Validate target format
        if not is_supported_format(target_format):
            return jsonify(create_response(error="Unsupported target format", status_code=400)), 400
        
        # Create transcode record
        transcode = Transcode(
            asset_id=asset_id,
            source_format=source_format,
            target_format=target_format,
            status='pending'
        )
        
        db.session.add(transcode)
        db.session.commit()
        
        # Start transcode job in background
        threading.Thread(target=process_transcode, args=(transcode.id,)).start()
        
        return jsonify(create_response(
            data=transcode_to_dict(transcode),
            message="Transcode job created successfully"
        )), 201
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating transcode: {e}")
        return jsonify(create_response(error="Failed to create transcode job", status_code=500)), 500

@app.route('/api/transcode/<int:transcode_id>', methods=['GET'])
@limiter.limit("200 per minute")
def get_transcode(transcode_id):
    """Get a specific transcode by ID"""
    try:
        transcode = Transcode.query.get(transcode_id)
        
        if not transcode:
            return jsonify(create_response(error="Transcode not found", status_code=404)), 404
        
        return jsonify(create_response(data=transcode_to_dict(transcode)))
    
    except Exception as e:
        logging.error(f"Error getting transcode {transcode_id}: {e}")
        return jsonify(create_response(error="Failed to retrieve transcode", status_code=500)), 500

@app.route('/api/transcode/<int:transcode_id>/cancel', methods=['POST'])
@limiter.limit("20 per minute")
def cancel_transcode(transcode_id):
    """Cancel a transcode job"""
    try:
        transcode = Transcode.query.get(transcode_id)
        
        if not transcode:
            return jsonify(create_response(error="Transcode not found", status_code=404)), 404
        
        if transcode.status in ['completed', 'failed']:
            return jsonify(create_response(error="Cannot cancel completed or failed job", status_code=400)), 400
        
        transcode.status = 'cancelled'
        transcode.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(create_response(message="Transcode job cancelled successfully"))
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error cancelling transcode {transcode_id}: {e}")
        return jsonify(create_response(error="Failed to cancel transcode", status_code=500)), 500

@app.route('/api/transcode/formats', methods=['GET'])
@limiter.limit("100 per minute")
def get_supported_formats():
    """Get supported transcode formats"""
    return jsonify(create_response(data=SUPPORTED_FORMATS))

def is_supported_format(format_name):
    """Check if format is supported"""
    for category, formats in SUPPORTED_FORMATS.items():
        if format_name.lower() in formats:
            return True
    return False

def process_transcode(transcode_id):
    """Process transcode job in background"""
    try:
        with app.app_context():
            transcode = Transcode.query.get(transcode_id)
            if not transcode:
                return
            
            # Update status to processing
            transcode.status = 'processing'
            transcode.progress = 0
            db.session.commit()
            
            # Get asset information (this would typically come from assets service)
            # For demo purposes, we'll simulate the process
            
            # Simulate transcode process
            for i in range(0, 101, 10):
                time.sleep(1)  # Simulate processing time
                transcode.progress = i
                db.session.commit()
            
            # Update status to completed
            transcode.status = 'completed'
            transcode.progress = 100
            transcode.output_path = f"{app.config['OUTPUT_FOLDER']}/transcoded_{transcode_id}.{transcode.target_format}"
            transcode.updated_at = datetime.utcnow()
            db.session.commit()
            
            logging.info(f"Transcode {transcode_id} completed successfully")
    
    except Exception as e:
        with app.app_context():
            transcode = Transcode.query.get(transcode_id)
            if transcode:
                transcode.status = 'failed'
                transcode.error_message = str(e)
                transcode.updated_at = datetime.utcnow()
                db.session.commit()
        
        logging.error(f"Error processing transcode {transcode_id}: {e}")

def transcode_to_dict(transcode):
    """Convert transcode object to dictionary"""
    return {
        "id": transcode.id,
        "asset_id": transcode.asset_id,
        "source_format": transcode.source_format,
        "target_format": transcode.target_format,
        "output_path": transcode.output_path,
        "status": transcode.status,
        "progress": transcode.progress,
        "error_message": transcode.error_message,
        "created_at": transcode.created_at.isoformat() if transcode.created_at else None,
        "updated_at": transcode.updated_at.isoformat() if transcode.updated_at else None
    }

@app.errorhandler(404)
def not_found(error):
    return jsonify(create_response(error="Endpoint not found", status_code=404)), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify(create_response(error="Internal server error", status_code=500)), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.getenv('TRANSCODE_SERVICE_PORT', 8003))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    ) 