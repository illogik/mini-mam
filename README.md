# Mini-MAM

A small demo Media Asset Management service  built with Flask, featuring assets, files, transcode, and search microservices and a react frontend.

<img width="1458" height="1203" alt="mini-mam" src="https://github.com/user-attachments/assets/b1072ae3-fd3a-47c2-a9e5-8019b8d904e1" />

This project was created using [Cursor](https://cursor.com/)

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

### Option 1: Docker (Recommended)

1. Build the docker images
```bash
make docker-build
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration:
# S3_BUCKET=your-bucket-name
# S3_REGION=us-east-1
# S3_ACCESS_KEY=your-access-key
# S3_SECRET_KEY=your-secret-key
# S3_ENDPOINT_URL=https://s3.amazonaws.com  # For AWS S3
# JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
# ADMIN_PASSWORD=your-admin-password
# USER_PASSWORD=your-user-password
```

3. Start the services
```bash
# Start all services
make docker-up
```

4. Access the service
Go to http://localhost:80

**Note**: The frontend uses host-relative URLs by default, so API calls will automatically use the same host as the frontend.

### Authentication

The API and frontend require authentication. Use the following credentials to get started:

- **Username**: `admin`
- **Password**: Set via `ADMIN_PASSWORD` environment variable (default: `admin123`)
- **Username**: `user`
- **Password**: Set via `USER_PASSWORD` environment variable (default: `user123`)

#### Frontend Authentication

The React frontend includes a complete authentication system:
- **Login Page**: Modern, responsive login interface
- **Demo Buttons**: Quick login with predefined credentials
- **User Display**: Shows current user and role in header
- **Auto-login**: Persistent sessions using localStorage
- **Protected Routes**: All features require authentication

See [AUTHENTICATION.md](AUTHENTICATION.md) for detailed backend authentication instructions.
See [src/frontend/AUTHENTICATION.md](src/frontend/AUTHENTICATION.md) for frontend authentication details.

### Option 2: Local Development

For local development without Docker, use the provided startup script:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start services locally:
```bash
# Start all services
python start_local.py

# Or start specific services
python start_local.py api-gateway assets-service
```

3. Access services:
- **API Gateway**: http://localhost:8000
- **Assets Service**: http://localhost:8001
- **Files Service**: http://localhost:8002
- **Transcode Service**: http://localhost:8003
- **Search Service**: http://localhost:8004 (requires authentication)
- **Frontend**: http://localhost:3000 (run separately with `npm start`)

4. Access metrics:
- **API Gateway Metrics**: http://localhost:9090/metrics
- **Assets Service Metrics**: http://localhost:9091/metrics
- **Files Service Metrics**: http://localhost:9092/metrics
- **Search Service Metrics**: http://localhost:9093/metrics
- **Transcode Service Metrics**: http://localhost:9094/metrics

## Deployment

### Using Pre-built Docker Images

The project includes GitHub Actions that automatically build and push Docker images to Docker Hub under the `iconikio` account.

#### Quick Start with Pre-built Images

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd mini-mam
   ```

2. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Run with pre-built images**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

#### Available Images

The following images are available on Docker Hub:
- `iconikio/mini-mam-api-gateway`
- `iconikio/mini-mam-assets-service`
- `iconikio/mini-mam-files-service`
- `iconikio/mini-mam-transcode-service`
- `iconikio/mini-mam-search-service`
- `iconikio/mini-mam-frontend`

#### Image Tags

- `main`: Latest from main branch
- `v1.0.0`: Semantic version tags
- `sha-abc123`: Commit-specific tags

### Building from Source

To build images locally:

```bash
# Build all services
docker-compose build

# Or build individual services
docker build -f docker/api-gateway.Dockerfile -t mini-mam-api-gateway .
docker build -f docker/assets-service.Dockerfile -t mini-mam-assets-service .
# ... etc
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
mini-mam/
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
python test_framework.py
```


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[BSD 3-clause License ](LICENSE)
