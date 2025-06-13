#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "Stopping port forwarding processes..."

# Services to stop
services=("shortener-service" "analytics-service" "prometheus-service" "grafana-service" "redis-service" "postgres-service")

for service in "${services[@]}"; do
    pid_file="/tmp/pf-$service.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log_info "Stopped port forward for $service (PID: $pid)"
        else
            log_error "Process $pid for $service not found"
        fi
        rm -f "$pid_file"
    else
        log_info "No PID file found for $service"
    fi
done

# Also kill any remaining kubectl port-forward processes
pkill -f "kubectl port-forward" 2>/dev/null || true

log_info "All port forwarding processes stopped"