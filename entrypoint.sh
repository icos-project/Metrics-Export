#!/bin/sh

# Default port if not provided
PORT=${PORT:-8000}

echo "🚀 Starting Gunicorn..."
exec gunicorn "src.main:app" -b "0.0.0.0:${PORT}" -k uvicorn.workers.UvicornWorker
