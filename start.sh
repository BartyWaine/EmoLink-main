#!/bin/bash
echo "Starting EmoLink deployment..."

# Wait for MySQL to be ready
echo "Waiting for MySQL..."
sleep 5

# Set PHP document root
export PHP_DOCUMENT_ROOT=/app/public

# Start Apache/PHP server
echo "Starting PHP server on port $PORT..."
exec php -S 0.0.0.0:$PORT -t /app/public
