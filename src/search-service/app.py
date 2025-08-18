from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.utils import setup_logging, create_response, construct_database_url
from shared.metrics import (
    setup_metrics_endpoint, record_request_metrics, metrics_middleware,
    db_operation_timer, cleanup_metrics
)
from prometheus_client import Counter
setup_logging("search-service")

app = Flask(__name__)
CORS(app)

# Search Service specific metrics
SEARCH_QUERIES = Counter(
    'search_queries_total',
    'Total number of search queries',
    ['query_type']
)

SEARCH_RESULTS = Counter(
    'search_results_total',
    'Total number of search results returned',
    ['query_type']
)

CONTENT_INDEXED = Counter(
    'content_indexed_total',
    'Total number of content items indexed',
    ['entity_type']
)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = construct_database_url('search_db')
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
metrics_port = int(os.getenv('SEARCH_SERVICE_METRICS_PORT', 9093))
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

# Create Flask-SQLAlchemy compatible SearchIndex model
class SearchIndex(db.Model):
    """Search index model for managing search data"""
    __tablename__ = 'search_indices'
    
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)  # asset, file, transcode
    entity_id = db.Column(db.Integer, nullable=False)
    search_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Initialize database tables
with app.app_context():
    db.create_all()

@app.route('/health', methods=['GET'])
@limiter.exempt
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "search-service",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/search', methods=['GET'])
@limiter.limit("200 per minute")
def search():
    """Search across all indexed content"""
    try:
        query = request.args.get('q', '')
        entity_type = request.args.get('type', '')  # asset, file, transcode
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'relevance')  # relevance, date, name
        sort_order = request.args.get('sort_order', 'desc')  # asc, desc
        
        if not query:
            return jsonify(create_response(error="Search query is required", status_code=400)), 400
        
        # Build search query - search in all indexed content
        # For now, we'll search in all records and filter in Python
        # This is a simple approach that works with both SQLite and PostgreSQL
        search_query = SearchIndex.query
        
        if entity_type:
            search_query = search_query.filter(SearchIndex.entity_type == entity_type)
        
        # Apply sorting
        if sort_by == 'date':
            search_query = search_query.order_by(SearchIndex.updated_at.desc() if sort_order == 'desc' else SearchIndex.updated_at.asc())
        elif sort_by == 'name':
            # This would need to be implemented based on your search data structure
            pass
        
        # Execute search and filter results
        with db_operation_timer('select', 'search_indices'):
            all_results = search_query.all()
        
        # Filter results in Python
        filtered_results = []
        for result in all_results:
            # Check if query matches in search_data
            search_data_str = str(result.search_data).lower()
            if query.lower() in search_data_str:
                filtered_results.append(result)
        
        # Record business metrics
        query_type = entity_type if entity_type else 'all'
        SEARCH_QUERIES.labels(query_type=query_type).inc()
        SEARCH_RESULTS.labels(query_type=query_type).inc(total)
        
        # Apply pagination manually
        total = len(filtered_results)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = filtered_results[start_idx:end_idx]
        
        # Process results
        search_results = []
        for result in paginated_results:
            search_data = result.search_data
            
            # Format search result to match frontend expectations
            formatted_result = {
                'id': str(result.entity_id),
                'title': search_data.get('name', search_data.get('title', 'Untitled')),
                'content': search_data.get('description', search_data.get('content', '')),
                'type': result.entity_type,
                'score': calculate_relevance_score(query, search_data),
                'metadata': search_data
            }
            search_results.append(formatted_result)
        
        # Sort by relevance if needed
        if sort_by == 'relevance':
            search_results.sort(key=lambda x: x.get('score', 0), reverse=(sort_order == 'desc'))
        
        # Calculate pagination info
        pages = (total + per_page - 1) // per_page  # Ceiling division
        
        return jsonify(create_response(
            data={
                "query": query,
                "results": search_results,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": pages
                }
            }
        ))
    
    except Exception as e:
        logging.error(f"Error performing search: {e}")
        return jsonify(create_response(error="Failed to perform search", status_code=500)), 500

@app.route('/api/search/index', methods=['POST'])
@limiter.limit("50 per minute")
def index_content():
    """Index content for search"""
    try:
        data = request.get_json()
        
        if not data or 'entity_type' not in data or 'entity_id' not in data or 'search_data' not in data:
            return jsonify(create_response(error="Entity type, ID, and search data are required", status_code=400)), 400
        
        entity_type = data['entity_type']
        entity_id = data['entity_id']
        search_data = data['search_data']
        
        # Check if index already exists
        existing_index = SearchIndex.query.filter_by(
            entity_type=entity_type, 
            entity_id=entity_id
        ).first()
        
        if existing_index:
            # Update existing index
            existing_index.search_data = search_data
            existing_index.updated_at = datetime.utcnow()
        else:
            # Create new index
            search_index = SearchIndex(
                entity_type=entity_type,
                entity_id=entity_id,
                search_data=search_data
            )
            db.session.add(search_index)
        
        db.session.commit()
        
        # Record business metric
        CONTENT_INDEXED.labels(entity_type=entity_type).inc()
        
        return jsonify(create_response(message="Content indexed successfully"))
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error indexing content: {e}")
        return jsonify(create_response(error="Failed to index content", status_code=500)), 500

@app.route('/api/search/index/<entity_type>/<int:entity_id>', methods=['DELETE'])
@limiter.limit("50 per minute")
def remove_index(entity_type, entity_id):
    """Remove content from search index"""
    try:
        search_index = SearchIndex.query.filter_by(
            entity_type=entity_type, 
            entity_id=entity_id
        ).first()
        
        if not search_index:
            return jsonify(create_response(error="Index not found", status_code=404)), 404
        
        db.session.delete(search_index)
        db.session.commit()
        
        return jsonify(create_response(message="Index removed successfully"))
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error removing index: {e}")
        return jsonify(create_response(error="Failed to remove index", status_code=500)), 500

@app.route('/api/search/suggestions', methods=['GET'])
@limiter.limit("100 per minute")
def get_suggestions():
    """Get search suggestions based on query"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query or len(query) < 2:
            return jsonify(create_response(data=[]))
        
        # Simple suggestion implementation
        # For production, consider using a dedicated search engine for better performance
        suggestions = []
        
        # Get recent searches or popular terms
        recent_searches = SearchIndex.query.filter(
            SearchIndex.search_data.contains(query)
        ).limit(limit).all()
        
        for search in recent_searches:
            search_data = search.search_data
            if 'name' in search_data:
                suggestions.append(search_data['name'])
            elif 'title' in search_data:
                suggestions.append(search_data['title'])
        
        return jsonify(create_response(data=suggestions))
    
    except Exception as e:
        logging.error(f"Error getting suggestions: {e}")
        return jsonify(create_response(error="Failed to get suggestions", status_code=500)), 500

@app.route('/api/search/analytics', methods=['GET'])
@limiter.limit("50 per minute")
def get_search_analytics():
    """Get search analytics"""
    try:
        # Get basic analytics
        total_indexed = SearchIndex.query.count()
        
        # Get counts by entity type
        asset_count = SearchIndex.query.filter_by(entity_type='asset').count()
        file_count = SearchIndex.query.filter_by(entity_type='file').count()
        transcode_count = SearchIndex.query.filter_by(entity_type='transcode').count()
        
        analytics = {
            "total_indexed": total_indexed,
            "by_type": {
                "assets": asset_count,
                "files": file_count,
                "transcodes": transcode_count
            }
        }
        
        return jsonify(create_response(data=analytics))
    
    except Exception as e:
        logging.error(f"Error getting analytics: {e}")
        return jsonify(create_response(error="Failed to get analytics", status_code=500)), 500

def calculate_relevance_score(query, search_data):
    """Calculate relevance score for search results"""
    score = 0
    query_lower = query.lower()
    
    # Check name/title
    if 'name' in search_data:
        name_lower = search_data['name'].lower()
        if query_lower in name_lower:
            score += 10
        if name_lower.startswith(query_lower):
            score += 5
    
    # Check description
    if 'description' in search_data:
        desc_lower = search_data['description'].lower()
        if query_lower in desc_lower:
            score += 3
    
    # Check tags
    if 'tags' in search_data and search_data['tags']:
        for tag in search_data['tags']:
            if query_lower in tag.lower():
                score += 2
    
    # Check type
    if 'type' in search_data:
        type_lower = search_data['type'].lower()
        if query_lower in type_lower:
            score += 1
    
    return score

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
    
    port = int(os.getenv('SEARCH_SERVICE_PORT', 8004))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    ) 