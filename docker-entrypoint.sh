#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Create necessary directories (as appuser)
mkdir -p /app/db
mkdir -p /app/data/user_directories
mkdir -p /app/staticfiles

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "Starting Gunicorn..."
gunicorn --bind 0.0.0.0:8008 app.wsgi:application