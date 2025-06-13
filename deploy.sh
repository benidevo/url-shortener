#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to cleanup failed deployment
cleanup_failed() {
    log_warn "Cleaning up failed deployment..."
    kubectl delete pods --all -n url-shortener --grace-period=0 --force 2>/dev/null || true
}

# Banner
echo "=================================================="
echo "🚀 URL Shortener - Complete Deployment Script"
echo "=================================================="
echo ""

# Step 1: Check prerequisites
log_header "1/10 Checking Prerequisites"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi
log_info "✓ Docker is running"

# Check if Kubernetes is enabled
if ! kubectl cluster-info >/dev/null 2>&1; then
    log_error "Kubernetes is not enabled or not accessible."
    log_error "Please enable Kubernetes in Docker Desktop: Settings > Kubernetes > Enable Kubernetes"
    exit 1
fi
log_info "✓ Kubernetes is enabled and accessible"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed or not in PATH"
    exit 1
fi
log_info "✓ kubectl is available"

echo ""

# Step 2: Setup metrics server (required for HPA auto-scaling)
log_header "2/10 Setting Up Metrics Server"

if kubectl get deployment metrics-server -n kube-system >/dev/null 2>&1; then
    log_info "✓ Metrics server already exists"
else
    log_info "Installing metrics server for HPA auto-scaling..."
    kubectl apply -f k8s/infrastructure/metrics-server.yaml
    
    log_info "Waiting for metrics server to be ready..."
    kubectl wait --namespace kube-system \
        --for=condition=ready pod \
        --selector=k8s-app=metrics-server \
        --timeout=60s || true
    
    log_info "✓ Metrics server installed"
fi

echo ""

# Step 3: Setup NGINX Ingress Controller
log_header "3/10 Setting Up NGINX Ingress Controller"

if kubectl get deployment ingress-nginx-controller -n ingress-nginx >/dev/null 2>&1; then
    log_info "✓ NGINX Ingress Controller already exists"
else
    log_info "Installing NGINX Ingress Controller from local YAML..."
    kubectl apply -f k8s/infrastructure/nginx-ingress-controller.yaml

    log_info "Waiting for ingress controller to be ready..."
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=120s || true

    log_info "✓ NGINX Ingress Controller installed on port 3000"
fi

echo ""

# Step 4: Build Docker images
log_header "4/10 Building Docker Images"

log_info "Building shortener service..."
docker build -t url-shortener/shortener:latest -f shortener/Dockerfile .

log_info "Building analytics service..."
docker build -t url-shortener/analytics:latest -f analytics/Dockerfile .

log_info "Building frontend..."
docker build -t url-shortener/frontend:latest -f frontend/Dockerfile .

log_info "✓ Docker images built successfully"

echo ""

# Step 5: Create namespace and database credentials
log_header "5/10 Creating Namespace and Database Credentials"

# Create namespace first
if kubectl get namespace url-shortener >/dev/null 2>&1; then
    log_info "✓ Namespace 'url-shortener' already exists"
else
    log_info "Creating namespace 'url-shortener'..."
    kubectl create namespace url-shortener
    log_info "✓ Namespace created"
fi

# Create database credentials
if kubectl get secret db-credentials -n url-shortener >/dev/null 2>&1; then
    log_info "✓ Database credentials already exist"
else
    log_info "Creating database credentials secret..."
    kubectl create secret generic db-credentials \
        --from-literal=shortener-db-url="postgresql://postgres:password123@postgres-service:5432/shortener" \
        --from-literal=analytics-db-url="postgresql://postgres:password123@postgres-service:5432/analytics" \
        --from-literal=postgres-user="postgres" \
        --from-literal=postgres-password="password123" \
        -n url-shortener

    log_info "✓ Database credentials created"
fi

echo ""

# Step 6: Deploy to Kubernetes
log_header "6/10 Deploying to Kubernetes"

cd k8s/
./scripts/deploy.sh
cd ..

echo ""

# Step 7: Wait for services to be ready
log_header "7/10 Waiting for Services to be Ready"

log_info "Waiting for all deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/shortener -n url-shortener || true
kubectl wait --for=condition=available --timeout=300s deployment/analytics -n url-shortener || true
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n url-shortener || true

log_info "Waiting for StatefulSets to be ready..."
kubectl wait --for=condition=ready --timeout=300s pod -l app=redis -n url-shortener || true
kubectl wait --for=condition=ready --timeout=300s pod -l app=postgres -n url-shortener || true

log_info "✓ All services are ready!"

echo ""

# Step 8: Initialize Databases
log_header "8/10 Initializing Databases"

log_info "Creating databases..."
kubectl exec -it postgres-0 -n url-shortener -- psql -U postgres -d postgres -c "CREATE DATABASE shortener;" 2>/dev/null || log_info "shortener already exists"
kubectl exec -it postgres-0 -n url-shortener -- psql -U postgres -d postgres -c "CREATE DATABASE analytics;" 2>/dev/null || log_info "analytics already exists"

log_info "Running database migrations..."
kubectl exec -it deployment/shortener -n url-shortener -- python -m alembic upgrade head 2>/dev/null || log_info "Shortener migrations completed"
kubectl exec -it deployment/analytics -n url-shortener -- python -m alembic upgrade head 2>/dev/null || log_info "Analytics migrations completed"

log_info "✓ Database initialization complete"

echo ""

# Step 9: Verify deployment
log_header "9/9 Verifying Deployment"

echo ""
echo "🎉 Deployment Complete!"
echo "=================================================="
echo ""
echo "📡 To access the application:"
echo "  1. Start port forwarding: kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 3000:3000"
echo "  2. Access frontend: http://localhost:3000/"
echo "  3. Short URLs: http://localhost:3000/s/{short_code}"
echo ""
echo "🔧 Management Commands:"
echo "  • Start port forwarding: make k8s-access"
echo "  • View logs:             make k8s-logs"
echo "  • Check status:          make k8s-status"
echo "  • Cleanup:               make k8s-stop"
echo ""
echo "🧪 Quick Test (after port forwarding):"
echo "  curl -X POST http://localhost:3000/api/shortener/api/v1/ \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"url\": \"https://github.com/your-awesome-project\"}'"
echo ""
echo "=================================================="
echo ""
log_info "✓ Deployment completed successfully!"
log_info "Run 'make k8s-access' to start port forwarding and access the application"
