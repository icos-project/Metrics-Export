#!/bin/sh

# Set default port if not specified
PORT=${PORT:-8000}

# Start Gunicorn
exec gunicorn "src.main:app" -b "0.0.0.0:${PORT}" -k uvicorn.workers.UvicornWorker
