# Metrics and Monitoring

This project includes comprehensive metrics collection for all Flask microservices using Prometheus with multiprocess support. Each service exposes metrics on a separate port for monitoring and observability.

## Architecture

The metrics system uses Prometheus multiprocess mode (`PROMETHEUS_MULTIPROC_DIR`) to properly collect metrics from multiple processes and workers:

- **Multiprocess Support**: Each service uses a shared metrics directory for proper metric aggregation
- **Process Isolation**: Each service has its own metrics directory to avoid conflicts
- **Automatic Cleanup**: Metrics files are automatically cleaned up when processes exit
- **Port Management**: Automatic port finding to avoid conflicts in local development

## Metrics Ports

Each service exposes metrics on the following ports:

| Service | Main Port | Metrics Port | Multiprocess Dir |
|---------|-----------|--------------|------------------|
| API Gateway | 8000 | 9090 | `/tmp/prometheus_multiproc` |
| Assets Service | 8001 | 9091 | `/tmp/prometheus_multiproc` |
| Files Service | 8002 | 9092 | `/tmp/prometheus_multiproc` |
| Search Service | 8004 | 9093 | `/tmp/prometheus_multiproc` |
| Transcode Service | 8003 | 9094 | `/tmp/prometheus_multiproc` |

## Accessing Metrics

You can access metrics for each service by visiting:

- **API Gateway Metrics**: http://localhost:9090/metrics
- **Assets Service Metrics**: http://localhost:9091/metrics
- **Files Service Metrics**: http://localhost:9092/metrics
- **Search Service Metrics**: http://localhost:9093/metrics
- **Transcode Service Metrics**: http://localhost:9094/metrics

## Available Metrics

### Shared Metrics (All Services)
- `http_requests_total`: Total number of HTTP requests by method, endpoint, and status
- `http_request_duration_seconds`: Request duration histogram by method and endpoint
- `http_requests_in_progress`: Number of currently active requests
- `database_operation_duration_seconds`: Database operation duration by operation type and table
- `database_connections_active`: Number of active database connections

### Service-Specific Business Metrics

#### API Gateway
- No additional business metrics (acts as proxy)

#### Assets Service
- `assets_created_total`: Total number of assets created
- `assets_updated_total`: Total number of assets updated
- `assets_deleted_total`: Total number of assets deleted
- `assets_retrieved_total`: Total number of assets retrieved

#### Files Service
- `files_uploaded_total`: Total number of files uploaded by file type
- `files_downloaded_total`: Total number of files downloaded
- `files_deleted_total`: Total number of files deleted
- `files_retrieved_total`: Total number of files retrieved

#### Search Service
- `search_queries_total`: Total number of search queries by query type
- `search_results_total`: Total number of search results returned by query type
- `content_indexed_total`: Total number of content items indexed by entity type

#### Transcode Service
- `transcode_jobs_total`: Total number of transcode jobs by status
- `transcode_duration_seconds`: Transcode job duration by source and target format
- `transcode_progress_percentage`: Transcode job progress percentage by status

## Example Metrics Output

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="health",status="200"} 42

# HELP assets_created_total Total number of assets created
# TYPE assets_created_total counter
assets_created_total 15

# HELP files_uploaded_total Total number of files uploaded
# TYPE files_uploaded_total counter
files_uploaded_total{file_type="image"} 8
files_uploaded_total{file_type="video"} 3

# HELP search_queries_total Total number of search queries
# TYPE search_queries_total counter
search_queries_total{query_type="all"} 25
search_queries_total{query_type="asset"} 10

# HELP transcode_jobs_total Total number of transcode jobs
# TYPE transcode_jobs_total counter
transcode_jobs_total{status="completed"} 12
transcode_jobs_total{status="failed"} 2
```

## Integration with Prometheus

To collect these metrics with Prometheus, add the following targets to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'assets-service'
    static_configs:
      - targets: ['localhost:9091']
  
  - job_name: 'files-service'
    static_configs:
      - targets: ['localhost:9092']
  
  - job_name: 'search-service'
    static_configs:
      - targets: ['localhost:9093']
  
  - job_name: 'transcode-service'
    static_configs:
      - targets: ['localhost:9094']
```

## Grafana Dashboards

You can create Grafana dashboards to visualize these metrics. Common dashboards include:

1. **Service Overview**: Request rates, response times, and error rates for all services
2. **Database Performance**: Database operation durations and connection counts
3. **Business Metrics by Service**:
   - **Assets**: Creation, update, deletion, and retrieval rates
   - **Files**: Upload/download patterns, file type distribution
   - **Search**: Query patterns, result counts, indexing rates
   - **Transcode**: Job success rates, duration patterns, format conversions
4. **Infrastructure**: Resource usage and system health

## Environment Variables

The metrics system can be configured using environment variables:

### Metrics Ports
- `API_GATEWAY_METRICS_PORT`: Metrics port for API Gateway (default: 9090)
- `ASSETS_SERVICE_METRICS_PORT`: Metrics port for Assets Service (default: 9091)
- `FILES_SERVICE_METRICS_PORT`: Metrics port for Files Service (default: 9092)
- `SEARCH_SERVICE_METRICS_PORT`: Metrics port for Search Service (default: 9093)
- `TRANSCODE_SERVICE_METRICS_PORT`: Metrics port for Transcode Service (default: 9094)

### Multiprocess Configuration
- `PROMETHEUS_MULTIPROC_DIR`: Directory for multiprocess metrics files (required for proper metric collection)

## Multiprocess Mode Benefits

### **Accurate Metrics Collection**
- Properly aggregates metrics from multiple processes/workers
- Avoids metric duplication or loss
- Handles process restarts gracefully

### **Production Ready**
- Works with Gunicorn, uWSGI, and other WSGI servers
- Supports multiple worker processes
- Handles containerized deployments

### **Automatic Management**
- Creates metrics directories automatically
- Cleans up temporary files on process exit
- Handles port conflicts in development

## Development vs Production

### **Development Mode**
- Uses temporary directories for metrics
- Automatic port finding to avoid conflicts
- Individual service metrics directories

### **Production Mode**
- Uses `/tmp/prometheus_multiproc` for all services
- Fixed port assignments
- Shared metrics directory for proper aggregation

## Troubleshooting

### **Port Already in Use**
The system automatically finds available ports. If you see port conflicts:
1. Check if other services are running
2. Use the local development script: `python start_local.py`
3. Verify environment variables are set correctly

### **Metrics Not Appearing**
1. Ensure `PROMETHEUS_MULTIPROC_DIR` is set
2. Check that the metrics directory is writable
3. Verify the service is running and accessible
4. Check service logs for metric-related errors

### **Cleanup Issues**
Metrics files are automatically cleaned up, but if you encounter issues:
```bash
# Manual cleanup (if needed)
sudo rm -rf /tmp/prometheus_multiproc*
```

The metrics system now properly supports multiprocess environments and provides accurate metric collection across all deployment scenarios. 