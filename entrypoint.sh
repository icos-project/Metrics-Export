#!/bin/sh

echo "⏳ Waiting for Grafana API Key Job to complete..."
TIMEOUT=600  # 10 minutes
ELAPSED=0

while true; do
  JOB_STATUS=$(kubectl get jobs -n ${HELM_RELEASE_NAMESPACE:-default} grafana-api-key-job -o jsonpath="{.status.succeeded}" 2>/dev/null)

  if [ "$JOB_STATUS" = "1" ]; then
    echo "✅ Grafana API Key Job has completed successfully!"
    break
  fi

  echo "🔄 Job not completed yet. Retrying in 10 seconds..."
  sleep 10
  ELAPSED=$((ELAPSED + 10))

  if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo "❌ Timeout: Grafana API Key Job did not complete after 10 minutes. Exiting."
    exit 1
  fi
done

# Default port if not provided
PORT=${PORT:-8000}

echo "🚀 Starting Gunicorn..."
exec gunicorn "src.main:app" -b "0.0.0.0:${PORT}" -k uvicorn.workers.UvicornWorker
