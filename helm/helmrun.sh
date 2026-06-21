#!/usr/bin/env bash
set -e

docker context use rancher-desktop
docker build -t kubefastapiapp:latest .

# Install or upgrade the release
if helm status myapp &>/dev/null; then
  echo "Release 'myapp' exists — upgrading..."
  helm upgrade myapp ./helm/fastapppkg
else
  echo "Installing release 'myapp'..."
  helm install myapp ./helm/fastapppkg
fi

echo ""
echo "Add to /etc/hosts if not already present:"
echo "  127.0.0.1  kubefastapiapp.test"
echo "  127.0.0.1  temporal.test"
echo ""
echo "Trigger a workflow:  curl -X POST http://kubefastapiapp.test/workflow/run"
echo "Temporal UI:         kubectl port-forward svc/myapp-temporal 7233:7233"
echo "                     docker run --rm -e TEMPORAL_ADDRESS=host.docker.internal:7233 -p 8080:8080 temporalio/ui:latest"
echo "                     open http://localhost:8080"
