#!/usr/bin/env bash
# Starts Temporal UI locally, accessible at http://localhost:8080
# Run this after helm/helmrun.sh

set -e

echo "Port-forwarding Temporal gRPC..."
kubectl port-forward svc/myapp-temporal 7233:7233 &
PF_PID=$!

# Give port-forward a moment to establish
sleep 2

echo "Starting Temporal UI at http://localhost:8080 ..."
docker run --rm \
  -e TEMPORAL_ADDRESS=host.docker.internal:7233 \
  -p 8080:8080 \
  --name temporal-ui \
  temporalio/ui:latest &
UI_PID=$!

echo ""
echo "Temporal UI: http://localhost:8080"
echo "Press Ctrl+C to stop."

# Stop both on exit
trap "kill $PF_PID $UI_PID 2>/dev/null" EXIT
wait $UI_PID
