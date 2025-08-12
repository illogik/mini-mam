FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/transcode-service/ ./transcode-service/
COPY src/shared/ ./shared/

# Create output and temp directories
RUN mkdir -p /app/transcoded /app/temp

# Create metrics directory
RUN mkdir -p /tmp/prometheus_multiproc

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app \
    && chown -R app:app /tmp/prometheus_multiproc
USER app

# Expose ports
EXPOSE 8003 9094

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["python", "transcode-service/app.py"] 