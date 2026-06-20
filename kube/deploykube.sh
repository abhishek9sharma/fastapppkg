#!/usr/bin/env bash
set -e

# Point docker CLI at minikube's daemon so the built image is available in-cluster
eval $(minikube docker-env)

# Rebuild the FastAPI image
docker stop $(docker ps | grep kubefastapiapp | awk '{print $1}') 2>/dev/null || true
docker container rm $(docker container ls -a | grep kubefastapiapp | awk '{print $1}') 2>/dev/null || true
docker image rm $(docker images | grep kubefastapiapp | awk '{print $3}') 2>/dev/null || true
docker build --tag kubefastapiapp .

# --- Postgres (must come first; Temporal init container waits for it) ---
kubectl apply -f kube/postgres-pvc.yaml
kubectl apply -f kube/postgres-deployment.yaml
kubectl apply -f kube/postgres-service.yaml

echo "Waiting for Postgres to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s

# --- Temporal (init container blocks until pg_isready, auto-setup runs migrations) ---
kubectl apply -f kube/temporal-deployment.yaml
kubectl apply -f kube/temporal-service.yaml
kubectl apply -f kube/temporal-ingress.yaml

echo "Waiting for Temporal to be ready..."
kubectl wait --for=condition=ready pod -l app=temporal --timeout=180s

# --- FastAPI + worker ---
kubectl apply -f kube/deployment.yaml
kubectl apply -f kube/service.yaml
kubectl apply -f kube/ingress.yaml

echo ""
echo "All services deployed."
echo "Add these to /etc/hosts if not already present:"
echo "  $(minikube ip)  kubefastapiapp.test"
echo "  $(minikube ip)  temporal.test"
echo ""
echo "Trigger a workflow:  curl -X POST http://kubefastapiapp.test/workflow/run"
echo "Temporal UI:         http://temporal.test"
echo "Temporal gRPC:       kubectl port-forward svc/temporal 7233:7233"
