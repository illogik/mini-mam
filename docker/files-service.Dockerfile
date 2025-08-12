FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libmagic1 \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/files-service/ ./files-service/
COPY src/shared/ ./shared/

# Create upload directory
RUN mkdir -p /app/uploads

# Create metrics directory
RUN mkdir -p /tmp/prometheus_multiproc

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app \
    && chown -R app:app /tmp/prometheus_multiproc
USER app

# Expose ports
EXPOSE 8002 9092

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["python", "files-service/app.py"] 