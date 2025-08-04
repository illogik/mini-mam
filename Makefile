# Flask Microservice Framework Makefile

.PHONY: help install start stop test clean docker-build docker-up docker-down logs

# Default target
help:
	@echo "Flask Microservice Framework - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     - Install Python dependencies"
	@echo "  start       - Start all services locally"
	@echo "  stop        - Stop all services"
	@echo "  test        - Run test suite"
	@echo "  verify      - Verify project structure"
	@echo "  clean       - Clean up temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up   - Start services with Docker Compose"
	@echo "  docker-down - Stop Docker services"
	@echo "  docker-restart - Restart Docker services"
	@echo "  docker-logs - View Docker logs"
	@echo ""
	@echo "Database:"
	@echo "  db-init     - Initialize databases"
	@echo "  db-migrate  - Run database migrations"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs        - View service logs"
	@echo "  status      - Check service status"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

# Start all services locally
start:
	@echo "Starting Flask Microservice Framework..."
	python start.py

# Stop all services
stop:
	@echo "Stopping services..."
	pkill -f "python.*app.py" || true

# Run tests
test:
	@echo "Running test suite..."
	python test_framework.py

# Verify structure
verify:
	@echo "Verifying project structure..."
	python verify_structure.py

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.db" -delete
	rm -rf uploads/ transcoded/ temp/ logs/

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-restart:
	@echo "Restarting Docker services..."
	docker-compose down
	docker-compose up -d

docker-logs:
	@echo "Viewing Docker logs..."
	docker-compose logs -f

# Database commands
db-init:
	@echo "Initializing databases..."
	@echo "This will be handled automatically by the services on first run"

db-migrate:
	@echo "Running database migrations..."
	@echo "Migrations are handled automatically by Flask-SQLAlchemy"

# Monitoring commands
logs:
	@echo "Viewing service logs..."
	@echo "Use 'docker-compose logs -f' for Docker logs"
	@echo "Or check individual service logs in their respective directories"

status:
	@echo "Checking service status..."
	@for service in api-gateway assets-service files-service transcode-service search-service; do \
		echo "Checking $$service..."; \
		curl -s http://localhost:$$(echo $$service | sed 's/-service//' | sed 's/api-gateway/8000/' | sed 's/assets/8001/' | sed 's/files/8002/' | sed 's/transcode/8003/' | sed 's/search/8004/')/health || echo "$$service is not responding"; \
	done

# Development helpers
dev-setup: install
	@echo "Setting up development environment..."
	cp env.example .env
	@echo "Please edit .env with your configuration"

dev-start: dev-setup
	@echo "Starting development environment..."
	python start.py

# Production helpers
prod-build: docker-build
	@echo "Production build completed"

prod-deploy: docker-up
	@echo "Production deployment completed"

# Utility commands
shell:
	@echo "Starting Python shell..."
	python

lint:
	@echo "Running linting..."
	flake8 . --exclude=venv,__pycache__,*.pyc
	black --check .
	mypy .

format:
	@echo "Formatting code..."
	black .
	isort .

# Service-specific commands
assets-logs:
	@echo "Assets service logs..."
	tail -f src/assets-service/app.log 2>/dev/null || echo "No log file found"

files-logs:
	@echo "Files service logs..."
	tail -f src/files-service/app.log 2>/dev/null || echo "No log file found"

transcode-logs:
	@echo "Transcode service logs..."
	tail -f src/transcode-service/app.log 2>/dev/null || echo "No log file found"

search-logs:
	@echo "Search service logs..."
	tail -f src/search-service/app.log 2>/dev/null || echo "No log file found"

gateway-logs:
	@echo "API Gateway logs..."
	tail -f src/api-gateway/app.log 2>/dev/null || echo "No log file found" 