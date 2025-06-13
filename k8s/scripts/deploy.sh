#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Change to k8s directory
cd "$(dirname "$0")/.."

log_info "Starting URL Shortener deployment..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    log_error "Not connected to a Kubernetes cluster"
    exit 1
fi

# Remind about image building
log_warn "Make sure you have built and pushed the application images:"
log_warn "  docker build -t url-shortener/shortener:latest ./shortener/"
log_warn "  docker build -t url-shortener/analytics:latest ./analytics/"
log_warn "  (Update deployment.yaml files if using a different registry)"
echo ""

# Deploy in order
log_info "Creating namespace..."
kubectl apply -f base/

log_info "Setting up RBAC..."
kubectl apply -f rbac.yaml

log_info "Applying network policies..."
kubectl apply -f network-policies.yaml

log_info "Creating secrets and configmaps..."
kubectl apply -f shared/

log_info "Deploying storage layer..."
kubectl apply -f storage/

log_info "Deploying application services..."
kubectl apply -f shortener/
kubectl apply -f analytics/
kubectl apply -f frontend/

log_info "Setting up monitoring..."
kubectl apply -f monitoring/

log_info "Creating Pod Disruption Budgets..."
kubectl apply -f pdb.yaml

log_info "Configuring ingress..."
kubectl apply -f shared/ingress-public.yaml

log_info "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/shortener -n url-shortener
kubectl wait --for=condition=available --timeout=300s deployment/analytics -n url-shortener
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n url-shortener
kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n url-shortener
kubectl wait --for=condition=available --timeout=300s deployment/grafana -n url-shortener

log_info "Waiting for StatefulSets to be ready..."
kubectl wait --for=condition=ready --timeout=300s pod -l app=redis -n url-shortener
kubectl wait --for=condition=ready --timeout=300s pod -l app=postgres -n url-shortener

log_info "Deployment completed successfully!"

log_info "Service endpoints:"
echo "  Shortener Service: kubectl port-forward service/shortener-service 8000:80 -n url-shortener"
echo "  Analytics Service: kubectl port-forward service/analytics-service 8001:80 -n url-shortener"
echo "  Prometheus: kubectl port-forward service/prometheus-service 9090:9090 -n url-shortener"
echo "  Grafana: kubectl port-forward service/grafana-service 3000:3000 -n url-shortener"

log_info "Use './scripts/port-forward.sh' to set up port forwarding"
log_info "Use './scripts/check-health.sh' to monitor health"
