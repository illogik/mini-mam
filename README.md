# Mini-MAM

A small demo Media Asset Management service  built with Flask, featuring assets, files, transcode, and search microservices and a react frontend.

## Architecture

- **Frontend**: React application served from root path
- **API Gateway**: Central entry point for all API requests
- **Assets Service**: Manages digital assets and metadata
- **Files Service**: Handles file uploads, storage, and retrieval
- **Transcode Service**: Processes and converts media files
- **Search Service**: Provides search functionality across all services

## Services

### API Gateway
- Route requests to appropriate microservices
- Handle authentication and authorization
- Rate limiting and request validation
- Load balancing

### Assets Service
- Asset metadata management
- Asset categorization and tagging
- Asset lifecycle management
- Asset versioning

### Files Service
- File upload and download
- **S3-based file storage** (AWS S3 or MinIO)
- File format validation
- File access control
- Cloud storage integration

### Transcode Service
- Media file conversion
- Video/audio processing
- Format optimization
- Batch processing

### Search Service
- Full-text search across assets
- Advanced filtering and sorting
- Search result ranking
- Search analytics

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start all services with Docker Compose:
```bash
docker-compose up
```

**Or** set up S3 storage manually:
   - **AWS S3**: Create an S3 bucket and configure AWS credentials
   - **Other S3-compatible services**: Configure your preferred S3-compatible storage

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your S3 configuration:
# S3_BUCKET=your-bucket-name
# S3_REGION=us-east-1
# S3_ACCESS_KEY=your-access-key
# S3_SECRET_KEY=your-secret-key
# S3_ENDPOINT_URL=https://s3.amazonaws.com  # For AWS S3
```

4. Build the docker images

```bash
make docker-build
```

5. Start the services
```bash
# Start all services
make docker-up
```



## Development

For development it is also possible to run all services locally

```bash

# Start individual services
python src/api-gateway/app.py
python src/assets-service/app.py
python src/files-service/app.py
python src/transcode-service/app.py
python src/search-service/app.py

# Or use the startup script
python start.py
```

## Access URLs

### Application
- **Frontend**: `http://localhost:80/`
- **API Gateway**: `http://localhost:80/api/`

### Services
- **Assets Service**: `http://localhost:80/api/assets/`
- **Files Service**: `http://localhost:80/api/files/`
- **Transcode Service**: `http://localhost:80/api/transcode/`
- **Search Service**: `http://localhost:80/api/search/`

### Storage
- **S3 Storage**: Configured via environment variables (AWS S3 or other S3-compatible services)

## API Documentation

Each service exposes RESTful APIs with comprehensive documentation available at:
- API Gateway: `http://localhost:80/api/docs`
- Assets Service: `http://localhost:80/assets/docs`
- Files Service: `http://localhost:80/files/docs`
- Transcode Service: `http://localhost:80/transcode/docs`
- Search Service: `http://localhost:80/search/docs`

## Development

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- PostgreSQL (for data persistence)
- **AWS S3 bucket** (or other S3-compatible storage service)

### Project Structure
```
flask-microservices/
├── src/                 # Source code directory
│   ├── frontend/        # React application
│   ├── api-gateway/     # API Gateway service
│   ├── assets-service/  # Assets management service
│   ├── files-service/   # File handling service
│   ├── transcode-service/ # Media transcoding service
│   ├── search-service/  # Search functionality service
│   └── shared/         # Shared utilities and models
├── config/              # Configuration files
├── docker/              # Docker configurations
├── requirements.txt      # Python dependencies
├── docker-compose.yml   # Service orchestration
└── README.md           # This file
```

### Access URLs

- **Frontend**: `http://localhost:80/` (main application)
- **API Gateway**: `http://localhost:80/api/` (all API endpoints)
- **Assets API**: `http://localhost:80/api/assets/`
- **Files API**: `http://localhost:80/api/files/`
- **Search API**: `http://localhost:80/api/search/`
- **Transcode API**: `http://localhost:80/api/transcode/`

## Testing

Run tests for all services:
```bash
pytest tests/
```

## Deployment

The framework includes Docker configurations for easy deployment:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License 
