# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=app.settings \
    PORT=8008

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user first
RUN useradd -m appuser

# Copy the project files and entrypoint script
COPY SingleCourseWebApp/ /app/
COPY docker-entrypoint.sh /app/
# Ensure the script has Unix-style line endings and is executable
RUN dos2unix /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Create all necessary directories
RUN mkdir -p /app/db && \
    mkdir -p /app/data/user_directories && \
    mkdir -p /app/staticfiles && \
    # Set ownership for all directories
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8008

ENTRYPOINT ["/app/docker-entrypoint.sh"] 