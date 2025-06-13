#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null; then
        return 1
    else
        return 0
    fi
}

# Function to start port forwarding
start_port_forward() {
    local service=$1
    local local_port=$2
    local remote_port=$3
    
    if check_port $local_port; then
        log_info "Starting port forward for $service on port $local_port"
        kubectl port-forward service/$service $local_port:$remote_port -n url-shortener &
        echo $! > /tmp/pf-$service.pid
    else
        log_warn "Port $local_port is already in use, skipping $service"
    fi
}

log_info "Setting up port forwarding for URL Shortener services..."

# Start port forwarding for all services
start_port_forward "shortener-service" 8000 80
start_port_forward "analytics-service" 8001 80
start_port_forward "prometheus-service" 9090 9090
start_port_forward "grafana-service" 3000 3000
start_port_forward "redis-service" 6379 6379
start_port_forward "postgres-service" 5432 5432

# Wait a moment for port forwards to establish
sleep 3

log_info "Port forwarding setup complete!"
echo ""
echo "Services available at:"
echo "  Shortener API: http://localhost:8000"
echo "  Analytics API: http://localhost:8001"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana: http://localhost:3000 (admin:admin123)"
echo "  Redis: localhost:6379"
echo "  PostgreSQL: localhost:5432"
echo ""
echo "To stop port forwarding, run: ./scripts/stop-port-forward.sh"
echo "To check service health, run: ./scripts/check-health.sh"