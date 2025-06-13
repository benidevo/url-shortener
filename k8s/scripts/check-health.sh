#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Function to check pod status
check_pods() {
    log_header "Pod Status:"
    kubectl get pods -n url-shortener -o wide
    echo ""
}

# Function to check services
check_services() {
    log_header "Service Status:"
    kubectl get services -n url-shortener
    echo ""
}

# Function to check HPA status
check_hpa() {
    log_header "Horizontal Pod Autoscaler Status:"
    kubectl get hpa -n url-shortener
    echo ""
}

# Function to check PDB status
check_pdb() {
    log_header "Pod Disruption Budget Status:"
    kubectl get pdb -n url-shortener
    echo ""
}

# Function to check resource usage
check_resources() {
    log_header "Resource Usage:"
    kubectl top pods -n url-shortener 2>/dev/null || log_warn "Metrics server not available"
    echo ""
}

# Function to check recent events
check_events() {
    log_header "Recent Events:"
    kubectl get events -n url-shortener --sort-by='.lastTimestamp' | tail -10
    echo ""
}

# Function to test service endpoints
test_endpoints() {
    log_header "Testing Service Endpoints:"
    
    # Check if services are reachable via port-forward
    services=("shortener-service:8000" "analytics-service:8001" "prometheus-service:9090" "grafana-service:3000")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        if curl -s --max-time 5 "http://localhost:$port/health" > /dev/null 2>&1; then
            log_info "$name: ✓ Healthy"
        else
            log_error "$name: ✗ Unhealthy or not accessible"
        fi
    done
    echo ""
}

# Function to show deployment status
check_deployments() {
    log_header "Deployment Status:"
    kubectl get deployments -n url-shortener
    echo ""
}

# Function to show statefulset status
check_statefulsets() {
    log_header "StatefulSet Status:"
    kubectl get statefulsets -n url-shortener
    echo ""
}

# Main execution
log_info "URL Shortener Health Check"
echo "=================================="

check_pods
check_deployments
check_statefulsets
check_services
check_hpa
check_pdb
check_resources
check_events

# Test endpoints only if port-forwarding is detected
if pgrep -f "kubectl port-forward" > /dev/null; then
    test_endpoints
else
    log_warn "No port-forwarding detected. Run './scripts/port-forward.sh' to test endpoints"
fi

log_info "Health check completed"