AWS_REGION?=us-east-1
ACCOUNT_ID?=079059455431
GIT_SHA?=$(shell git rev-parse --short HEAD 2>/dev/null || echo 0.1)
REGISTRY?=$(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

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

###################
### ci commands ###
###################

ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(REGISTRY)

# api-gateway
.PHONY: build-ci-api-gateway push-ci-api-gateway release-ci-api-gateway
build-ci-api-gateway:
	docker build -f docker/api-gateway.Dockerfile -t $(REGISTRY)/api-gateway:$(GIT_SHA) .

push-ci-api-gateway: ecr-login
	docker push $(REGISTRY)/api-gateway:$(GIT_SHA)

release-ci-api-gateway: build-ci-api-gateway push-ci-api-gateway

# assets-service
.PHONY: build-ci-assets-service push-ci-assets-service release-ci-assets-service
build-ci-assets-service:
	docker build -f docker/assets-service.Dockerfile -t $(REGISTRY)/assets-service:$(GIT_SHA) .

push-ci-assets-service: ecr-login
	docker push $(REGISTRY)/assets-service:$(GIT_SHA)

release-ci-assets-service: build-ci-assets-service push-ci-assets-service

# files-service
.PHONY: build-ci-files-service push-ci-files-service release-ci-files-service
build-ci-files-service:
	docker build -f docker/files-service.Dockerfile -t $(REGISTRY)/files-service:$(GIT_SHA) .

push-ci-files-service: ecr-login
	docker push $(REGISTRY)/files-service:$(GIT_SHA)

release-ci-files-service: build-ci-files-service push-ci-files-service

# search-service
.PHONY: build-ci-search-service push-ci-search-service release-ci-search-service
build-ci-search-service:
	docker build -f docker/search-service.Dockerfile -t $(REGISTRY)/search-service:$(GIT_SHA) .

push-ci-search-service: ecr-login
	docker push $(REGISTRY)/search-service:$(GIT_SHA)

release-ci-search-service: build-ci-search-service push-ci-search-service

# transcode-service
.PHONY: build-ci-transcode-service push-ci-transcode-service release-ci-transcode-service
build-ci-transcode-service:
	docker build -f docker/transcode-service.Dockerfile -t $(REGISTRY)/transcode-service:$(GIT_SHA) .

push-ci-transcode-service: ecr-login
	docker push $(REGISTRY)/transcode-service:$(GIT_SHA)

release-ci-transcode-service: build-ci-transcode-service push-ci-transcode-service

# frontend
.PHONY: build-ci-frontend push-ci-frontend release-ci-frontend
build-ci-frontend:
	docker build -f src/frontend/Dockerfile -t $(REGISTRY)/frontend:$(GIT_SHA) src/frontend

push-ci-frontend: ecr-login
	docker push $(REGISTRY)/frontend:$(GIT_SHA)

release-ci-frontend: build-ci-frontend push-ci-frontend

# rollups
.PHONY: build-ci-all push-ci-all release-ci-all
build-ci-all: build-ci-api-gateway build-ci-assets-service build-ci-files-service build-ci-search-service build-ci-transcode-service build-ci-frontend
push-ci-all:  push-ci-api-gateway  push-ci-assets-service  push-ci-files-service  push-ci-search-service  push-ci-transcode-service push-ci-frontend
release-ci-all: release-ci-api-gateway release-ci-assets-service release-ci-files-service release-ci-search-service release-ci-transcode-service release-ci-frontend

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
