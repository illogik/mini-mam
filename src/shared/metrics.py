from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, multiprocess
from flask import Response
import time
import threading
import os
import tempfile
from functools import wraps

# Set up multiprocess metrics directory
def setup_multiprocess_metrics():
    """Setup multiprocess metrics directory"""
    if 'PROMETHEUS_MULTIPROC_DIR' not in os.environ:
        # Create a temporary directory for metrics
        metrics_dir = tempfile.mkdtemp(prefix='prometheus_multiproc_')
        os.environ['PROMETHEUS_MULTIPROC_DIR'] = metrics_dir
        return metrics_dir
    
    metrics_dir = os.environ['PROMETHEUS_MULTIPROC_DIR']
    
    # Ensure the directory exists
    if not os.path.exists(metrics_dir):
        try:
            os.makedirs(metrics_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create metrics directory {metrics_dir}: {e}")
            # Fallback to temporary directory
            fallback_dir = tempfile.mkdtemp(prefix='prometheus_multiproc_')
            os.environ['PROMETHEUS_MULTIPROC_DIR'] = fallback_dir
            return fallback_dir
    
    return metrics_dir

# Initialize multiprocess metrics
setup_multiprocess_metrics()

# Create a multiprocess-aware registry
def get_registry():
    """Get the multiprocess-aware registry"""
    return multiprocess.MultiProcessCollector(CollectorRegistry())

# Global metrics with multiprocess support
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently in progress',
    ['method', 'endpoint']
)

# Database metrics
DB_OPERATION_DURATION = Histogram(
    'database_operation_duration_seconds',
    'Database operation duration in seconds',
    ['operation', 'table']
)

DB_CONNECTIONS_ACTIVE = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

def metrics_middleware():
    """Flask middleware to collect request metrics"""
    def middleware(request):
        start_time = time.time()
        
        # Increment active requests
        ACTIVE_REQUESTS.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).inc()
        
        return start_time
    
    return middleware

def record_request_metrics(start_time, request, response):
    """Record request metrics after response"""
    duration = time.time() - start_time
    
    # Decrement active requests
    ACTIVE_REQUESTS.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown'
    ).dec()
    
    # Record request count and duration
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown'
    ).observe(duration)

def metrics_decorator(f):
    """Decorator to automatically record metrics for a function"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        # Record function call
        REQUEST_COUNT.labels(
            method='FUNCTION',
            endpoint=f.__name__,
            status='200'
        ).inc()
        
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            # Record error
            REQUEST_COUNT.labels(
                method='FUNCTION',
                endpoint=f.__name__,
                status='500'
            ).inc()
            raise
        finally:
            # Record duration
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method='FUNCTION',
                endpoint=f.__name__
            ).observe(duration)
    
    return decorated_function

def db_operation_timer(operation, table):
    """Context manager for timing database operations"""
    class DBTimer:
        def __init__(self, operation, table):
            self.operation = operation
            self.table = table
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            DB_CONNECTIONS_ACTIVE.inc()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            DB_OPERATION_DURATION.labels(
                operation=self.operation,
                table=self.table
            ).observe(duration)
            DB_CONNECTIONS_ACTIVE.dec()
    
    return DBTimer(operation, table)

def get_metrics_response():
    """Generate Prometheus metrics response with multiprocess support"""
    registry = get_registry()
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

def setup_metrics_endpoint(app, port=9090):
    """Setup metrics endpoint and start metrics server on separate port"""
    from prometheus_client import start_http_server
    import socket
    
    # Add metrics endpoint to main app
    @app.route('/metrics', methods=['GET'])
    def metrics():
        return get_metrics_response()
    
    # Find an available port
    def find_available_port(start_port):
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + 100):  # Try up to 100 ports
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        return None
    
    # Start metrics server on separate port
    def start_metrics_server():
        available_port = find_available_port(port)
        if available_port:
            try:
                # Use multiprocess registry for the metrics server
                registry = get_registry()
                start_http_server(available_port, registry=registry)
                print(f"Metrics server started on port {available_port}")
            except Exception as e:
                print(f"Failed to start metrics server on port {available_port}: {e}")
        else:
            print(f"Could not find available port starting from {port}")
    
    # Start metrics server in a separate thread
    metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
    metrics_thread.start()
    
    return metrics_thread

def cleanup_metrics():
    """Clean up metrics files when process exits"""
    import atexit
    import shutil
    
    def cleanup():
        metrics_dir = os.environ.get('PROMETHEUS_MULTIPROC_DIR')
        if metrics_dir and os.path.exists(metrics_dir):
            try:
                shutil.rmtree(metrics_dir)
            except Exception as e:
                print(f"Warning: Could not cleanup metrics directory {metrics_dir}: {e}")
    
    atexit.register(cleanup) 