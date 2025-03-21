#!/bin/sh

echo "⏳ Waiting for Grafana API Key Job to complete..."
TIMEOUT=600  # 10 minutes
ELAPSED=0

while true; do
  echo "HELM_RELEASE_NAMESPACE: ${HELM_RELEASE_NAMESPACE}"

  COMPLETION_STATUS=$(kubectl get jobs -n ${HELM_RELEASE_NAMESPACE} grafana-api-key-job -o jsonpath="{.status.conditions[?(@.type=='Complete')].status}" 2>/dev/null)
  echo "🔍 COMPLETION_STATUS: ${COMPLETION_STATUS}"

  RAW_JOB_OUTPUT=$(kubectl get jobs -n ${HELM_RELEASE_NAMESPACE} grafana-api-key-job -o jsonpath="{.status.succeeded}" 2>&1)
  echo "🔍 RAW JOB OUTPUT: '$RAW_JOB_OUTPUT'"
  JOB_STATUS=$(echo "$RAW_JOB_OUTPUT" | tr -d '\n' | tr -d '\r')  # Remove any weird newlines

  export HELM_RELEASE_NAMESPACE1=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
  echo "HELM_RELEASE_NAMESPACE1: ${HELM_RELEASE_NAMESPACE1}"
  echo "Test2"
  COMPLETION_STATUS=$(kubectl get jobs -n ${HELM_RELEASE_NAMESPACE} grafana-api-key-job -o jsonpath="{.status.conditions[?(@.type=='Complete')].status}" 2>/dev/null)
  echo "🔍 COMPLETION_STATUS: ${COMPLETION_STATUS}"

  RAW_JOB_OUTPUT=$(kubectl get jobs -n ${HELM_RELEASE_NAMESPACE} grafana-api-key-job -o jsonpath="{.status.succeeded}" 2>&1)
  echo "🔍 RAW JOB OUTPUT: '$RAW_JOB_OUTPUT'"
  JOB_STATUS=$(echo "$RAW_JOB_OUTPUT" | tr -d '\n' | tr -d '\r')  # Remove any weird newlines

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
