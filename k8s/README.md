# Kubernetes Deployment Guide

## Overview

This directory contains production-ready Kubernetes manifests for the URL Shortener application with the following features:

- **Security Hardening**: RBAC, Network Policies, Pod Security
- **High Availability**: HPA, PDB, Rolling Updates
- **Observability**: Prometheus + Grafana monitoring
- **Persistent Storage**: StatefulSets for Redis and PostgreSQL

## Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- Docker for building images
- Metrics server (for HPA)

## Building Images

Before deployment, build and push the application images:

```bash
# Build shortener service
docker build -t url-shortener/shortener:latest ./shortener/
docker tag url-shortener/shortener:latest your-registry/url-shortener/shortener:latest
docker push your-registry/url-shortener/shortener:latest

# Build analytics service
docker build -t url-shortener/analytics:latest ./analytics/
docker tag url-shortener/analytics:latest your-registry/url-shortener/analytics:latest
docker push your-registry/url-shortener/analytics:latest
```

**Note**: Update the image references in the deployment files if using a different registry.

## Deployment

### Quick Start

```bash
# Deploy everything
./scripts/deploy.sh

# Set up local access
./scripts/port-forward.sh

# Check health
./scripts/check-health.sh
```

### Manual Deployment

```bash
# 1. Create namespace and RBAC
kubectl apply -f base/
kubectl apply -f rbac.yaml

# 2. Apply security policies
kubectl apply -f network-policies.yaml

# 3. Create secrets and configs
kubectl apply -f shared/

# 4. Deploy storage layer
kubectl apply -f storage/

# 5. Deploy applications
kubectl apply -f shortener/
kubectl apply -f analytics/

# 6. Set up monitoring
kubectl apply -f monitoring/

# 7. Configure high availability
kubectl apply -f pdb.yaml
```

## Configuration

### Secrets

Create the required secrets before deployment:

```bash
kubectl create secret generic db-credentials \
  --from-literal=shortener-db-url="postgresql://user:pass@postgres-service:5432/shortener" \
  --from-literal=analytics-db-url="postgresql://user:pass@postgres-service:5432/analytics" \
  --from-literal=postgres-user="postgres" \
  --from-literal=postgres-password="your-password" \
  -n url-shortener
```

### ConfigMaps

Update ConfigMaps in `shared/` directory for environment-specific settings.

## Accessing Services

With port-forwarding enabled:

- **Shortener API**: http://localhost:8000
- **Analytics API**: http://localhost:8001
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin:admin123)

## Monitoring

- **Prometheus**: Collects metrics from all services
- **Grafana**: Provides dashboards for monitoring health and performance
- **Health Checks**: All services have proper health probes configured

## Security Features

- **Non-root containers** with read-only filesystems
- **Network policies** for service isolation
- **RBAC** with minimal permissions
- **Pod security contexts** with dropped capabilities
- **Resource limits** for proper resource management

## High Availability

- **Horizontal Pod Autoscaler** for automatic scaling
- **Pod Disruption Budgets** for availability during maintenance
- **Rolling updates** for zero-downtime deployments
- **Multiple replicas** for fault tolerance

## Troubleshooting

```bash
# Check pod status
kubectl get pods -n url-shortener

# View logs
kubectl logs -f deployment/shortener -n url-shortener
kubectl logs -f deployment/analytics -n url-shortener

# Check events
kubectl get events -n url-shortener --sort-by='.lastTimestamp'

# Debug network issues
kubectl exec -it pod-name -n url-shortener -- /bin/sh
```

## Cleanup

```bash
# Remove all resources
kubectl delete namespace url-shortener

# Stop port forwarding
./scripts/stop-port-forward.sh
```
