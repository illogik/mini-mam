from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import tempfile
import io

# Load environment variables
load_dotenv()

# Setup logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.utils import (
    setup_logging, create_response, calculate_file_hash, 
    get_file_size, get_mime_type, sanitize_filename, ensure_directory_exists
)
from shared.metrics import (
    setup_metrics_endpoint, record_request_metrics, metrics_middleware,
    db_operation_timer
)
from prometheus_client import Counter
setup_logging("files-service")

app = Flask(__name__)
CORS(app)

# Files Service specific metrics
FILES_UPLOADED = Counter(
    'files_uploaded_total',
    'Total number of files uploaded',
    ['file_type']
)

FILES_DOWNLOADED = Counter(
    'files_downloaded_total',
    'Total number of files downloaded'
)

FILES_DELETED = Counter(
    'files_deleted_total',
    'Total number of files deleted'
)

FILES_RETRIEVED = Counter(
    'files_retrieved_total',
    'Total number of files retrieved'
)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///files.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# S3 Configuration
app.config['S3_BUCKET'] = os.getenv('S3_BUCKET', 'mini-mam-files')
app.config['S3_REGION'] = os.getenv('S3_REGION', 'us-east-1')
app.config['S3_ACCESS_KEY'] = os.getenv('S3_ACCESS_KEY')
app.config['S3_SECRET_KEY'] = os.getenv('S3_SECRET_KEY')
app.config['S3_ENDPOINT_URL'] = os.getenv('S3_ENDPOINT_URL')  # For local testing with MinIO

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'mp3', 'wav'}

db = SQLAlchemy(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)

# Setup metrics
metrics_port = int(os.getenv('FILES_SERVICE_METRICS_PORT', 9092))
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

# Create Flask-SQLAlchemy compatible File model
class File(db.Model):
    """File model for managing file uploads and storage"""
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    s3_key = db.Column(db.String(500), nullable=False)  # S3 object key instead of file path
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    checksum = db.Column(db.String(64))
    asset_id = db.Column(db.Integer)  # Reference to asset, but no foreign key constraint
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

# Initialize database tables
with app.app_context():
    db.create_all()

# S3 Client initialization
def get_s3_client():
    """Get S3 client with configuration"""
    config = {
        'region_name': app.config['S3_REGION']
    }
    
    if app.config['S3_ACCESS_KEY'] and app.config['S3_SECRET_KEY']:
        config['aws_access_key_id'] = app.config['S3_ACCESS_KEY']
        config['aws_secret_access_key'] = app.config['S3_SECRET_KEY']
    
    if app.config['S3_ENDPOINT_URL']:
        config['endpoint_url'] = app.config['S3_ENDPOINT_URL']
    
    return boto3.client('s3', **config)

def upload_to_s3(file_data, s3_key, content_type=None):
    """Upload file data to S3"""
    try:
        s3_client = get_s3_client()
        
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        s3_client.upload_fileobj(
            file_data,
            app.config['S3_BUCKET'],
            s3_key,
            ExtraArgs=extra_args
        )
        return True
    except (ClientError, NoCredentialsError) as e:
        logging.error(f"Error uploading to S3: {e}")
        return False

def download_from_s3(s3_key):
    """Download file data from S3"""
    try:
        s3_client = get_s3_client()
        
        response = s3_client.get_object(
            Bucket=app.config['S3_BUCKET'],
            Key=s3_key
        )
        return response['Body']
    except ClientError as e:
        logging.error(f"Error downloading from S3: {e}")
        return None

def delete_from_s3(s3_key):
    """Delete file from S3"""
    try:
        s3_client = get_s3_client()
        
        s3_client.delete_object(
            Bucket=app.config['S3_BUCKET'],
            Key=s3_key
        )
        return True
    except ClientError as e:
        logging.error(f"Error deleting from S3: {e}")
        return False

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "files-service",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/files', methods=['GET'])
@limiter.limit("100 per minute")
def get_files():
    """Get all files with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        asset_id = request.args.get('asset_id', type=int)
        mime_type = request.args.get('mime_type', '')
        
        query = File.query.filter(File.is_active == True)
        
        if asset_id:
            query = query.filter(File.asset_id == asset_id)
        
        if mime_type:
            query = query.filter(File.mime_type.contains(mime_type))
        
        files = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify(create_response(
            data={
                "files": [file_to_dict(file) for file in files.items],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": files.total,
                    "pages": files.pages
                }
            }
        ))
    
    except Exception as e:
        logging.error(f"Error getting files: {e}")
        return jsonify(create_response(error="Failed to retrieve files", status_code=500)), 500

@app.route('/api/files/presigned-url', methods=['POST'])
@limiter.limit("50 per minute")
def generate_presigned_url():
    """Generate a pre-signed URL for direct S3 upload"""
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify(create_response(error="Filename is required", status_code=400)), 400
        
        filename = data['filename']
        if not allowed_file(filename):
            return jsonify(create_response(error="File type not allowed", status_code=400)), 400
        
        # Secure the filename
        from werkzeug.utils import secure_filename
        secure_name = secure_filename(filename)
        
        # Generate unique filename and S3 key
        from shared.utils import generate_uuid
        unique_filename = f"{generate_uuid()}_{secure_name}"
        s3_key = f"uploads/{unique_filename}"
        
        # Generate pre-signed URL for upload
        s3_client = get_s3_client()
        
        # Create pre-signed URL for PUT operation (upload)
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': app.config['S3_BUCKET'],
                'Key': s3_key,
                'ContentType': data.get('content_type', 'application/octet-stream')
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )
        
        return jsonify(create_response(
            data={
                'presigned_url': presigned_url,
                's3_key': s3_key,
                'unique_filename': unique_filename,
                'original_filename': filename
            },
            message="Pre-signed URL generated successfully"
        ))
    
    except Exception as e:
        logging.error(f"Error generating pre-signed URL: {e}")
        return jsonify(create_response(error="Failed to generate pre-signed URL", status_code=500)), 500

@app.route('/api/files/<int:file_id>/presigned-url', methods=['GET'])
@limiter.limit("200 per minute")
def get_presigned_download_url(file_id):
    """Generate a pre-signed URL for downloading a file"""
    try:
        file_record = File.query.filter_by(id=file_id, is_active=True).first()
        
        if not file_record:
            return jsonify(create_response(error="File not found", status_code=404)), 404
        
        # Generate pre-signed URL for download
        s3_client = get_s3_client()
        
        # Create pre-signed URL for GET operation (download)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': app.config['S3_BUCKET'],
                'Key': file_record.s3_key
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )
        
        return jsonify(create_response(
            data={
                'presigned_url': presigned_url,
                'filename': file_record.original_filename,
                'content_type': file_record.mime_type
            },
            message="Pre-signed download URL generated successfully"
        ))
    
    except Exception as e:
        logging.error(f"Error generating pre-signed download URL for file {file_id}: {e}")
        return jsonify(create_response(error="Failed to generate pre-signed download URL", status_code=500)), 500

@app.route('/api/files', methods=['POST'])
@limiter.limit("20 per minute")
def upload_file():
    """Upload a new file"""
    try:
        if 'file' not in request.files:
            return jsonify(create_response(error="No file provided", status_code=400)), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify(create_response(error="No file selected", status_code=400)), 400
        
        if not allowed_file(file.filename):
            return jsonify(create_response(error="File type not allowed", status_code=400)), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        original_filename = file.filename
        
        # Generate unique filename and S3 key
        from shared.utils import generate_uuid
        unique_filename = f"{generate_uuid()}_{filename}"
        s3_key = f"uploads/{unique_filename}"
        
        # Get file information from memory
        file_content = file.read()
        file_size = len(file_content)
        mime_type = file.content_type or 'application/octet-stream'
        
        # Calculate checksum from memory
        import hashlib
        checksum = hashlib.sha256(file_content).hexdigest()
        
        # Upload to S3
        file.seek(0)  # Reset file pointer
        if not upload_to_s3(file, s3_key, mime_type):
            return jsonify(create_response(error="Failed to upload file to S3", status_code=500)), 500
        
        # Create file record
        file_record = File(
            filename=unique_filename,
            original_filename=original_filename,
            s3_key=s3_key,
            file_size=file_size,
            mime_type=mime_type,
            checksum=checksum,
            asset_id=request.form.get('asset_id', type=int)
        )
        
        with db_operation_timer('insert', 'files'):
            db.session.add(file_record)
            db.session.commit()
        
        # Record business metric
        file_type = mime_type.split('/')[0] if '/' in mime_type else 'unknown'
        FILES_UPLOADED.labels(file_type=file_type).inc()
        
        return jsonify(create_response(
            data=file_to_dict(file_record),
            message="File uploaded successfully"
        )), 201
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error uploading file: {e}")
        return jsonify(create_response(error="Failed to upload file", status_code=500)), 500

@app.route('/api/files/complete-upload', methods=['POST'])
@limiter.limit("50 per minute")
def complete_upload():
    """Complete file upload by creating database record"""
    try:
        data = request.get_json()
        if not data or 's3_key' not in data or 'original_filename' not in data:
            return jsonify(create_response(error="Missing required fields", status_code=400)), 400
        
        s3_key = data['s3_key']
        original_filename = data['original_filename']
        unique_filename = data.get('unique_filename', '')
        file_size = data.get('file_size', 0)
        mime_type = data.get('mime_type', 'application/octet-stream')
        checksum = data.get('checksum', '')
        asset_id = data.get('asset_id')
        
        # Verify file exists in S3
        s3_object = download_from_s3(s3_key)
        if not s3_object:
            return jsonify(create_response(error="File not found in S3", status_code=404)), 404
        
        # Create file record
        file_record = File(
            filename=unique_filename or s3_key.split('/')[-1],
            original_filename=original_filename,
            s3_key=s3_key,
            file_size=file_size,
            mime_type=mime_type,
            checksum=checksum,
            asset_id=asset_id
        )
        
        db.session.add(file_record)
        db.session.commit()
        
        return jsonify(create_response(
            data=file_to_dict(file_record),
            message="File upload completed successfully"
        )), 201
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error completing upload: {e}")
        return jsonify(create_response(error="Failed to complete upload", status_code=500)), 500

@app.route('/api/files/<int:file_id>', methods=['GET'])
@limiter.limit("200 per minute")
def get_file(file_id):
    """Get a specific file by ID"""
    try:
        file_record = File.query.filter_by(id=file_id, is_active=True).first()
        
        if not file_record:
            return jsonify(create_response(error="File not found", status_code=404)), 404
        
        # Record business metric
        FILES_RETRIEVED.inc()
        
        return jsonify(create_response(data=file_to_dict(file_record)))
    
    except Exception as e:
        logging.error(f"Error getting file {file_id}: {e}")
        return jsonify(create_response(error="Failed to retrieve file", status_code=500)), 500

@app.route('/api/files/<int:file_id>/download', methods=['GET'])
@limiter.limit("100 per minute")
def download_file(file_id):
    """Download a file from S3"""
    try:
        file_record = File.query.filter_by(id=file_id, is_active=True).first()
        
        if not file_record:
            return jsonify(create_response(error="File not found", status_code=404)), 404
        
        # Download from S3
        s3_object = download_from_s3(file_record.s3_key)
        if not s3_object:
            return jsonify(create_response(error="File not found in S3", status_code=404)), 404
        
        # Create a temporary file-like object
        file_data = io.BytesIO(s3_object.read())
        file_data.seek(0)
        
        # Record business metric
        FILES_DOWNLOADED.inc()
        
        return send_file(
            file_data,
            as_attachment=True,
            download_name=file_record.original_filename,
            mimetype=file_record.mime_type
        )
    
    except Exception as e:
        logging.error(f"Error downloading file {file_id}: {e}")
        return jsonify(create_response(error="Failed to download file", status_code=500)), 500

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@limiter.limit("20 per minute")
def delete_file(file_id):
    """Delete a file (soft delete)"""
    try:
        file_record = File.query.filter_by(id=file_id, is_active=True).first()
        
        if not file_record:
            return jsonify(create_response(error="File not found", status_code=404)), 404
        
        # Soft delete
        file_record.is_active = False
        file_record.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Delete from S3 (optional - you might want to keep files in S3 for backup)
        delete_from_s3(file_record.s3_key)
        FILES_DELETED.inc()
        
        return jsonify(create_response(message="File deleted successfully"))
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting file {file_id}: {e}")
        return jsonify(create_response(error="Failed to delete file", status_code=500)), 500

@app.route('/api/files/<int:file_id>/validate', methods=['POST'])
@limiter.limit("50 per minute")
def validate_file(file_id):
    """Validate file integrity from S3"""
    try:
        file_record = File.query.filter_by(id=file_id, is_active=True).first()
        
        if not file_record:
            return jsonify(create_response(error="File not found", status_code=404)), 404
        
        # Download from S3 for validation
        s3_object = download_from_s3(file_record.s3_key)
        if not s3_object:
            return jsonify(create_response(error="File not found in S3", status_code=404)), 404
        
        # Read file content and calculate checksum
        file_content = s3_object.read()
        current_checksum = hashlib.sha256(file_content).hexdigest()
        current_size = len(file_content)
        
        # Validate
        is_valid = (
            current_checksum == file_record.checksum and
            current_size == file_record.file_size
        )
        
        return jsonify(create_response(
            data={
                "is_valid": is_valid,
                "checksum_match": current_checksum == file_record.checksum,
                "size_match": current_size == file_record.file_size,
                "current_checksum": current_checksum,
                "current_size": current_size
            }
        ))
    
    except Exception as e:
        logging.error(f"Error validating file {file_id}: {e}")
        return jsonify(create_response(error="Failed to validate file", status_code=500)), 500

def file_to_dict(file_record):
    """Convert file object to dictionary"""
    return {
        "id": file_record.id,
        "filename": file_record.filename,
        "original_filename": file_record.original_filename,
        "s3_key": file_record.s3_key,
        "file_size": file_record.file_size,
        "mime_type": file_record.mime_type,
        "checksum": file_record.checksum,
        "asset_id": file_record.asset_id,
        "created_at": file_record.created_at.isoformat() if file_record.created_at else None,
        "updated_at": file_record.updated_at.isoformat() if file_record.updated_at else None
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
    
    port = int(os.getenv('FILES_SERVICE_PORT', 8002))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    ) 