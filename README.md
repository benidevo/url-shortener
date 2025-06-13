# URL Shortener with Analytics

A production-ready distributed URL shortening system with geographic analytics, built using microservices architecture, FastAPI, and Kubernetes.

## 🏗️ Architecture

![Architecture Diagram](architecture.png)

### Core Components

- **Shortener Service**: FastAPI service for URL shortening and redirection
- **Analytics Service**: gRPC-enabled service for usage analytics and geographic tracking
- **PostgreSQL**: Persistent storage with separate databases per service
- **Redis**: Caching layer for improved performance
- **Prometheus + Grafana**: Monitoring and observability stack

### Key Features

✅ **Production-Ready Kubernetes Deployment**

- Security hardening (RBAC, Network Policies, Pod Security)
- Auto-scaling with Horizontal Pod Autoscaler
- High availability with Pod Disruption Budgets
- Health probes and rolling updates

✅ **Microservices Architecture**

- Independent scaling and deployment
- gRPC inter-service communication
- RESTful APIs for external clients

✅ **Observability & Monitoring**

- Prometheus metrics collection
- Grafana dashboards
- Structured logging with correlation IDs

## 🚀 Quick Start

### Prerequisites

1. **Docker Desktop** with Kubernetes enabled
   - Go to Docker Desktop > Settings > Kubernetes > Enable Kubernetes
2. **Git** for cloning the repository

### One-Command Deployment (Recommended)

#### Option 1: Using Make (Recommended)

```bash
# Clone and deploy everything
git clone <your-repo-url>
cd url-shortener

# Deploy to Kubernetes
make k8s-deploy

# Check status
make k8s-status

# View logs
make k8s-logs

# Stop everything (removes all deployment resources)
make k8s-stop
```

#### Option 2: Direct script execution

```bash
# Clone and deploy everything
git clone <your-repo-url>
cd url-shortener
./deploy.sh
```

**Both options handle:**

- ✅ Prerequisites checking
- ✅ Docker image building
- ✅ Database credentials creation
- ✅ Kubernetes deployment
- ✅ Port forwarding setup
- ✅ Health verification

### 🎯 Available Make Commands

```bash
# Show all available commands
make help

# Kubernetes deployment
make k8s-deploy     # Deploy everything
make k8s-status     # Check status
make k8s-logs       # View logs
make k8s-stop       # Remove all resources
make k8s-restart    # Stop and redeploy

# Docker Compose (local development)
make build          # Build and start services
make up             # Start services
make down           # Stop services
make test           # Run tests
```

### Alternative: Local Development (Docker Compose)

For simple local development without Kubernetes:

```bash
# Start all services with Docker Compose
docker compose up --build -d
make db-init-and-migrate

# Access services directly
- Shortener API: http://localhost:8000/docs
- Analytics API: http://localhost:8001/docs
- Frontend: http://localhost:3000
```

## 📡 API Usage

### Kubernetes Deployment (Recommended)

After deploying with `make k8s-deploy`, access via the frontend at **<http://localhost:3000>**:

```bash
# Use the web interface for URL shortening and analytics
open http://localhost:3000

# For development/testing - API endpoints through frontend proxy:
curl -X POST http://localhost:3000/api/shortener/api/v1/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/your-awesome-project"}'
```

### Docker Compose (Local Development)

When using `docker compose up`, services are accessible on individual ports:

```bash
# Create short URL (direct API access)
curl -X POST http://localhost:8000/api/v1/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/your-awesome-project"}'

# Access short URL
curl -L http://localhost:8000/api/v1/abc123

# Get analytics
curl http://localhost:8001/api/v1/abc123

# Frontend UI
open http://localhost:3000
```

## 🛠️ Development

### Local Development Commands

```bash
# Start development environment
make up

# Run database migrations
make db-migrate

# Format code
make format

# Run tests
make test

# Access service shells
make into_shortener
make into_analytics

# View logs
make logs
```

### Project Structure

```plaintext
├── shortener/          # URL shortening service
├── analytics/          # Analytics service
├── k8s/               # Kubernetes manifests
│   ├── scripts/       # Deployment automation
│   ├── monitoring/    # Prometheus & Grafana
│   └── storage/       # StatefulSets for databases
├── frontend/          # Simple web interface
├── proto/             # gRPC protocol definitions
└── docker-compose.yaml
```

## 🔒 Security Features

- **Non-root containers** with read-only filesystems
- **Network policies** for service isolation
- **RBAC** with minimal permissions
- **Resource limits** and security contexts
- **Secret management** for sensitive data

## 📊 Monitoring & Observability

### Access Monitoring Stack

```bash
# With port-forwarding enabled
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin:admin123)
```

### Key Metrics

- HTTP request rates and latency
- Database connection pool status
- Pod resource utilization
- Service health and availability

## 🌐 Production Deployment

### Cloud Provider Setup

**AWS EKS:**

```bash
eksctl create cluster --name url-shortener --region us-west-2
```

**Google GKE:**

```bash
gcloud container clusters create url-shortener --zone us-central1-a
```

**Azure AKS:**

```bash
az aks create --resource-group myResourceGroup --name url-shortener
```

### Image Registry

```bash
# Push to your registry
docker tag url-shortener/shortener:latest your-registry/shortener:latest
docker push your-registry/shortener:latest

# Update k8s/*/deployment.yaml with your registry URLs
```

## 🧪 Testing

```bash
# Unit tests
make test-unit

# Integration tests
make test-integration

# Load testing
make test-load

# Health check (Docker Compose)
curl http://localhost:8000/health
curl http://localhost:8001/health

# Health check (Kubernetes)
make k8s-status
```

## 🚨 Troubleshooting

### Common Issues

**Pods stuck in Pending:**

```bash
kubectl describe pods -n url-shortener
kubectl get events -n url-shortener --sort-by='.lastTimestamp'
```

**Database connection errors:**

```bash
kubectl logs -f deployment/postgres -n url-shortener
kubectl exec -it postgres-0 -n url-shortener -- psql -U postgres
```

**Image pull errors:**

```bash
# For Docker Desktop Kubernetes (rebuild images)
docker build -t url-shortener/shortener:latest ./shortener/
docker build -t url-shortener/analytics:latest ./analytics/

# For cloud deployments
docker push your-registry/shortener:latest
```

### Health Checks

```bash
# Check all services
./k8s/scripts/check-health.sh

# Individual service logs
kubectl logs -f deployment/shortener -n url-shortener
kubectl logs -f deployment/analytics -n url-shortener
```

## 🧹 Cleanup

```bash
# Stop port forwarding
./k8s/scripts/stop-port-forward.sh

# Remove Kubernetes resources
kubectl delete namespace url-shortener

# Stop local development
make down_volumes
```
