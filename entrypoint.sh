#!/bin/sh

# Set default port if not specified
PORT=${PORT:-8000}

# Start Gunicorn
exec gunicorn "metrics_generator:app_dispatch" -b "0.0.0.0:${PORT}" -w 4
